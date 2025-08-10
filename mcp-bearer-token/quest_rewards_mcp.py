# Quest & Rewards MCP Server for Puch AI
# A gamified quest system with XP, rewards, and fun challenges!

import asyncio
from typing import Annotated, Optional, Literal, List
import os, uuid, json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
import random

from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from mcp import ErrorData, McpError
from mcp.types import TextContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import Field, BaseModel

# --- Environment Setup ---
load_dotenv()
TOKEN = os.environ.get("AUTH_TOKEN", "your_secret_token_here")
MY_NUMBER = os.environ.get("MY_NUMBER", "919876543210")
REVIEW_TOKEN = os.environ.get("REVIEW_TOKEN", TOKEN)
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB", "ecohero")

# --- Auth Provider (matches starter kit behavior) ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="quest-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# --- MCP Server Setup ---
mcp = FastMCP(
    "Quest & Rewards MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Data Models ---
class User(BaseModel):
    user_id: str
    name: str
    total_xp: int = 0
    daily_xp: int = 0
    last_daily_reset: str
    quests_completed: List[str] = []
    streak_days: int = 0
    last_quest_date: Optional[str] = None
    created_at: str

class Quest(BaseModel):
    quest_id: str
    title: str
    description: str
    xp_reward: int
    quest_type: Literal["climate", "social", "personal"]
    verification_method: Literal["manual", "auto"] = "manual"
    created_by: str  # "admin" or user_id
    is_golden: bool = False
    program: Optional[str] = None  # e.g., "eco_hero"
    created_at: str

class Reward(BaseModel):
    reward_id: str
    title: str
    xp_required: int
    reward_type: Literal["voucher", "tshirt", "sticker", "badge"]
    given_to: List[str] = []
    created_at: str

class Submission(BaseModel):
    submission_id: str
    quest_id: str
    user_id: str
    proof_url: Optional[str] = None
    proof_text: Optional[str] = None
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    reviewed_at: Optional[str] = None

# --- In-Memory Storage (replace with database in production) ---
USERS: dict[str, User] = {}
QUESTS: dict[str, Quest] = {}
REWARDS: dict[str, Reward] = {}
SUBMISSIONS: dict[str, Submission] = {}

mongo_client: MongoClient | None = None
db = None

# --- Utility Functions ---
def _now() -> str:
    return datetime.utcnow().isoformat()

def _get_user(puch_user_id: str) -> User:
    if not puch_user_id:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="puch_user_id is required"))
    
    if puch_user_id not in USERS:
        # Create new user with fun onboarding
        user = User(
            user_id=puch_user_id,
            name=f"Adventurer_{puch_user_id[:8]}",
            total_xp=0,
            daily_xp=0,
            last_daily_reset=_now(),
            quests_completed=[],
            streak_days=0,
            created_at=_now()
        )
        USERS[puch_user_id] = user
        if db:
            db.users.update_one({"user_id": puch_user_id}, {"$set": user.model_dump()}, upsert=True)
    
    return USERS[puch_user_id]

def _has_approved_submission(user_id: str, quest_id: str) -> bool:
    for submission in SUBMISSIONS.values():
        if submission.user_id == user_id and submission.quest_id == quest_id and submission.status == "approved":
            return True
    return False

def _reset_daily_xp_if_needed(user: User):
    """Reset daily XP if it's a new day"""
    last_reset = datetime.fromisoformat(user.last_daily_reset.replace('Z', '+00:00'))
    now = datetime.utcnow()
    
    if (now - last_reset).days >= 1:
        user.daily_xp = 0
        user.last_daily_reset = _now()
        
        # Check streak
        if user.last_quest_date:
            last_quest = datetime.fromisoformat(user.last_quest_date.replace('Z', '+00:00'))
            if (now - last_quest).days == 1:
                user.streak_days += 1
            elif (now - last_quest).days > 1:
                user.streak_days = 0

def _calculate_xp_gain(user: User, quest_xp: int) -> int:
    """Calculate actual XP gain considering daily limit"""
    remaining_daily = 15 - user.daily_xp
    if remaining_daily <= 0:
        return 0
    
    # Apply streak bonus
    streak_bonus = min(user.streak_days // 7, 3)  # Max 3 bonus XP for 7+ day streak
    
    total_gain = min(quest_xp + streak_bonus, remaining_daily)
    return total_gain

def _get_fun_response(emoji: str, message: str) -> str:
    """Add fun elements to responses"""
    fun_prefixes = [
        "🎉", "🌟", "✨", "🎊", "🔥", "💪", "🚀", "🎯", "🏆", "💎"
    ]
    return f"{random.choice(fun_prefixes)} {emoji} {message}"

# --- Initialize Default Content ---
def _initialize_default_content():
    """Create default quests and rewards"""
    if not QUESTS:
        default_quests = [
            Quest(
                quest_id="plant_tree",
                title="🌱 Plant a Tree",
                description="Plant a tree in your community or backyard to help the environment!",
                xp_reward=5,
                quest_type="climate",
                verification_method="manual",
                program="eco_hero",
                created_by="admin",
                created_at=_now()
            ),
            Quest(
                quest_id="reduce_plastic",
                title="♻️ Reduce Plastic Use",
                description="Use a reusable water bottle instead of plastic bottles for a day",
                xp_reward=3,
                quest_type="climate",
                created_by="admin",
                created_at=_now()
            ),
            Quest(
                quest_id="recycle_electronics",
                title="📱 Recycle Electronics",
                description="Properly recycle old electronics or donate them",
                xp_reward=4,
                quest_type="climate",
                created_by="admin",
                created_at=_now()
            ),
            Quest(
                quest_id="help_neighbor",
                title="🤝 Help a Neighbor",
                description="Offer help to a neighbor or community member",
                xp_reward=3,
                quest_type="social",
                created_by="admin",
                created_at=_now()
            ),
            Quest(
                quest_id="study_2_hours",
                title="📚 Study for 2 Hours",
                description="Dedicate 2 hours to studying or learning something new",
                xp_reward=4,
                quest_type="personal",
                created_by="admin",
                created_at=_now()
            )
        ]
        
        for quest in default_quests:
            QUESTS[quest.quest_id] = quest
            if db:
                db.quests.update_one({"quest_id": quest.quest_id}, {"$set": quest.model_dump()}, upsert=True)
    
    if not REWARDS:
        default_rewards = [
            Reward(
                reward_id="first_quest",
                title="🎯 First Quest Badge",
                xp_required=0,
                reward_type="badge",
                created_at=_now()
            ),
            Reward(
                reward_id="eco_warrior",
                title="🌍 Eco Warrior Sticker",
                xp_required=25,
                reward_type="sticker",
                created_at=_now()
            ),
            Reward(
                reward_id="streak_master",
                title="🔥 Streak Master T-Shirt",
                xp_required=100,
                reward_type="tshirt",
                created_at=_now()
            ),
            Reward(
                reward_id="xp_champion",
                title="🏆 XP Champion Voucher",
                xp_required=500,
                reward_type="voucher",
                created_at=_now()
            )
        ]
        
        for reward in default_rewards:
            REWARDS[reward.reward_id] = reward
            if db:
                db.rewards.update_one({"reward_id": reward.reward_id}, {"$set": reward.model_dump()}, upsert=True)

# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- Tool Descriptions ---
REGISTER_USER_DESCRIPTION = RichToolDescription(
    description="Register a new user with a fun onboarding experience",
    use_when="A new user wants to start their quest journey",
    side_effects="Creates a new user profile with 0 XP"
)

CREATE_QUEST_DESCRIPTION = RichToolDescription(
    description="Create a new quest (admin or personal)",
    use_when="User wants to create a new challenge for themselves or others",
    side_effects="Adds a new quest to the system"
)

LIST_QUESTS_DESCRIPTION = RichToolDescription(
    description="List available quests with filters",
    use_when="User wants to see available challenges",
    side_effects="None"
)

COMPLETE_QUEST_DESCRIPTION = RichToolDescription(
    description="Complete a quest and earn XP",
    use_when="User has finished a challenge and wants to claim rewards",
    side_effects="Awards XP and updates user progress"
)

USER_PROFILE_DESCRIPTION = RichToolDescription(
    description="View user profile with XP, streak, and achievements",
    use_when="User wants to check their progress and stats",
    side_effects="None"
)

LIST_REWARDS_DESCRIPTION = RichToolDescription(
    description="List available rewards and user's earned rewards",
    use_when="User wants to see what rewards they can unlock",
    side_effects="None"
)

CLAIM_REWARD_DESCRIPTION = RichToolDescription(
    description="Claim a reward if user has enough XP",
    use_when="User wants to unlock a reward they've earned",
    side_effects="Marks reward as claimed for the user"
)

ECO_SUBMIT_DESCRIPTION = RichToolDescription(
    description="Submit proof for a quest (Eco Hero program)",
    use_when="User uploads a link/text as proof of completing an eco/social task",
    side_effects="Creates a pending submission for review"
)

ECO_REVIEW_DESCRIPTION = RichToolDescription(
    description="Review a submission (approve/reject) and award XP",
    use_when="Admin/reviewer validates user proof for eco/social tasks",
    side_effects="Awards XP on approval and updates streak"
)

# --- Tools ---

@mcp.tool
async def validate() -> str:
    return MY_NUMBER

@mcp.tool
async def health_check() -> str:
    return "🎮 Quest & Rewards MCP Server is running! All systems operational! ⚡"

@mcp.tool(description=ECO_SUBMIT_DESCRIPTION.model_dump_json())
async def submit_proof(
    puch_user_id: Annotated[str, Field(description="User ID")],
    quest_id: Annotated[str, Field(description="Quest ID")],
    proof_url: Annotated[Optional[str], Field(description="URL to image/video/article")]=None,
    proof_text: Annotated[Optional[str], Field(description="Short description of the proof")]=None,
) -> list[TextContent]:
    try:
        if quest_id not in QUESTS:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Quest not found"))
        if not proof_url and not proof_text:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Provide proof_url or proof_text"))
        _get_user(puch_user_id)
        submission = Submission(
            submission_id=str(uuid.uuid4()),
            quest_id=quest_id,
            user_id=puch_user_id,
            proof_url=proof_url,
            proof_text=proof_text,
            status="pending",
            created_at=_now()
        )
        SUBMISSIONS[submission.submission_id] = submission
        if db:
            db.submissions.update_one({"submission_id": submission.submission_id}, {"$set": submission.model_dump()}, upsert=True)
        return [TextContent(type="text", text=f"📥 Submission received! ID: `{submission.submission_id}`. A reviewer will validate it soon.")]
    except McpError:
        raise
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=ECO_REVIEW_DESCRIPTION.model_dump_json())
async def review_submission(
    reviewer_id: Annotated[str, Field(description="Reviewer/Admin ID")],
    submission_id: Annotated[str, Field(description="Submission ID")],
    approve: Annotated[bool, Field(description="Approve or reject")],
    notes: Annotated[Optional[str], Field(description="Optional notes")]=None,
) -> list[TextContent]:
    try:
        if submission_id not in SUBMISSIONS:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Submission not found"))
        submission = SUBMISSIONS[submission_id]
        if submission.status != "pending":
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Submission already reviewed"))
        submission.status = "approved" if approve else "rejected"
        submission.reviewer_id = reviewer_id
        submission.notes = notes
        submission.reviewed_at = _now()
        if db:
            db.submissions.update_one({"submission_id": submission.submission_id}, {"$set": submission.model_dump()}, upsert=True)

        quest = QUESTS.get(submission.quest_id)
        user = _get_user(submission.user_id)

        awarded_text = ""
        if approve and quest:
            _reset_daily_xp_if_needed(user)
            xp_gain = _calculate_xp_gain(user, quest.xp_reward)
            user.daily_xp += xp_gain
            user.total_xp += xp_gain
            if quest.quest_id not in user.quests_completed:
                user.quests_completed.append(quest.quest_id)
            user.last_quest_date = _now()
            if db:
                db.users.update_one({"user_id": user.user_id}, {"$set": user.model_dump()}, upsert=True)
            awarded_text = f" ✅ Awarded {xp_gain} XP for '{quest.title}'."

        return [TextContent(type="text", text=f"🧪 Review: {submission.status.upper()} for submission `{submission_id}`.{awarded_text}")]
    except McpError:
        raise
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=REGISTER_USER_DESCRIPTION.model_dump_json())
async def register_user(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    name: Annotated[str, Field(description="User's display name")],
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        user.name = name
        
        welcome_message = (
            f"🎉 **Welcome to Eco Hero, {name}!** 🌍\n\n"
            f"Here’s how it works:\n"
            f"1) Pick a quest (climate, social, or personal).\n"
            f"2) If it requires proof, use /submit_proof (URL or short text).\n"
            f"3) A reviewer approves it → you earn XP.\n\n"
            f"⚡ Daily cap: 15 XP | 🌟 Golden quests: 2x XP | 🔥 Streaks: bonus XP\n\n"
            f"📊 **Your Stats:**\n"
            f"   • Total XP: {user.total_xp} 🏆\n"
            f"   • Daily XP: {user.daily_xp}/15 ⚡\n"
            f"   • Streak: {user.streak_days} days 🔥\n\n"
            f"🚀 Try: /list_quests puch_user_id={user.user_id}"
        )
        
        return [TextContent(type="text", text=welcome_message)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=CREATE_QUEST_DESCRIPTION.model_dump_json())
async def create_quest(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    title: Annotated[str, Field(description="Quest title")],
    description: Annotated[str, Field(description="Quest description")],
    xp_reward: Annotated[int, Field(description="XP reward for completing this quest")],
    quest_type: Annotated[Literal["climate", "social", "personal"], Field(description="Type of quest")],
    is_golden: Annotated[bool, Field(description="Whether this is a golden quest (double XP)")] = False,
) -> list[TextContent]:
    try:
        if not title or not title.strip():
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Title cannot be empty"))
        
        if xp_reward <= 0 or xp_reward > 20:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="XP reward must be between 1 and 20"))
        
        quest_id = str(uuid.uuid4())
        quest = Quest(
            quest_id=quest_id,
            title=title.strip(),
            description=description.strip(),
            xp_reward=xp_reward * 2 if is_golden else xp_reward,
            quest_type=quest_type,
            created_by=puch_user_id,
            is_golden=is_golden,
            created_at=_now()
        )
        
        QUESTS[quest_id] = quest
        if db:
            db.quests.update_one({"quest_id": quest_id}, {"$set": quest.model_dump()}, upsert=True)
        
        golden_text = "🌟 **GOLDEN QUEST** 🌟" if is_golden else ""
        response = (
            f"{golden_text}\n"
            f"🎯 **Quest Created Successfully!**\n\n"
            f"📝 **Title:** {quest.title}\n"
            f"📖 **Description:** {quest.description}\n"
            f"🏆 **XP Reward:** {quest.xp_reward} XP\n"
            f"🏷️ **Type:** {quest.quest_type.title()}\n"
            f"🆔 **Quest ID:** `{quest_id}`\n\n"
            f"💡 **Share this ID with others to let them complete your quest!**"
        )
        
        return [TextContent(type="text", text=response)]
    except McpError:
        raise
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=LIST_QUESTS_DESCRIPTION.model_dump_json())
async def list_quests(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    quest_type: Annotated[Optional[Literal["climate", "social", "personal"]], Field(description="Filter by quest type")] = None,
    show_completed: Annotated[bool, Field(description="Show completed quests")] = False,
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        _reset_daily_xp_if_needed(user)
        
        available_quests = []
        for quest in QUESTS.values():
            if quest_type and quest.quest_type != quest_type:
                continue
            
            is_completed = quest.quest_id in user.quests_completed
            if is_completed and not show_completed:
                continue
            
            quest_info = {
                "quest_id": quest.quest_id,
                "title": quest.title,
                "description": quest.description,
                "xp_reward": quest.xp_reward,
                "quest_type": quest.quest_type,
                "is_golden": quest.is_golden,
                "is_completed": is_completed,
                "created_by": quest.created_by
            }
            available_quests.append(quest_info)
        
        if not available_quests:
            response = "📭 **No quests found!** Create your first quest to get started! 🎯"
        else:
            response = f"📋 **Available Quests** ({len(available_quests)} found)\n\n"
            
            for quest in available_quests:
                status_emoji = "✅" if quest["is_completed"] else "🎯"
                golden_emoji = "🌟" if quest["is_golden"] else ""
                type_emoji = {"climate": "🌱", "social": "🤝", "personal": "📚"}[quest["quest_type"]]
                
                response += (
                    f"{status_emoji} **{quest['title']}** {golden_emoji}\n"
                    f"   📖 {quest['description']}\n"
                    f"   🏆 {quest['xp_reward']} XP | {type_emoji} {quest['quest_type'].title()}\n"
                    f"   🆔 `{quest['quest_id']}`\n\n"
                )
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=COMPLETE_QUEST_DESCRIPTION.model_dump_json())
async def complete_quest(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    quest_id: Annotated[str, Field(description="Quest ID to complete")],
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        _reset_daily_xp_if_needed(user)
        
        if quest_id not in QUESTS:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Quest {quest_id} not found"))
        
        if quest_id in user.quests_completed:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Quest already completed"))
        
        quest = QUESTS[quest_id]
        # Require approved proof for manual-verification quests
        if getattr(quest, "verification_method", "manual") == "manual":
            if not _has_approved_submission(puch_user_id, quest_id):
                return [TextContent(
                    type="text",
                    text=(
                        "📝 This quest requires manual verification.\n\n"
                        "📥 Submit proof first using:\n"
                        f"   /submit_proof puch_user_id={puch_user_id} quest_id={quest_id} proof_url=<link> (or) proof_text=\"what you did\"\n\n"
                        "✅ A reviewer will approve it and XP will be awarded automatically."
                    ),
                )]
        xp_gain = _calculate_xp_gain(user, quest.xp_reward)
        
        if xp_gain == 0:
            response = (
                f"⚠️ **Daily XP Limit Reached!**\n\n"
                f"📊 **Your Stats:**\n"
                f"   • Daily XP: {user.daily_xp}/15 ⚡\n"
                f"   • Total XP: {user.total_xp} 🏆\n\n"
                f"💡 **Come back tomorrow to earn more XP!**"
            )
        else:
            # Award XP
            user.daily_xp += xp_gain
            user.total_xp += xp_gain
            user.quests_completed.append(quest_id)
            user.last_quest_date = _now()
            if db:
                db.users.update_one({"user_id": user.user_id}, {"$set": user.model_dump()}, upsert=True)
            
            # Check for new rewards
            new_rewards = []
            for reward in REWARDS.values():
                if (user.total_xp >= reward.xp_required and 
                    puch_user_id not in reward.given_to):
                    new_rewards.append(reward)
            
            # Build response
            golden_text = "🌟 **GOLDEN QUEST COMPLETED!** 🌟" if quest.is_golden else ""
            streak_bonus = min(user.streak_days // 7, 3)
            
            response = (
                f"{golden_text}\n"
                f"🎉 **Quest Completed Successfully!**\n\n"
                f"🏆 **Quest:** {quest.title}\n"
                f"📖 **Description:** {quest.description}\n"
                f"⚡ **XP Earned:** {xp_gain} XP\n"
                f"   • Base XP: {quest.xp_reward}\n"
                f"   • Streak Bonus: +{streak_bonus} XP\n\n"
                f"📊 **Updated Stats:**\n"
                f"   • Daily XP: {user.daily_xp}/15 ⚡\n"
                f"   • Total XP: {user.total_xp} 🏆\n"
                f"   • Streak: {user.streak_days} days 🔥\n"
            )
            
            if new_rewards:
                response += f"\n🎁 **New Rewards Unlocked!**\n"
                for reward in new_rewards:
                    response += f"   • {reward.title} 🎯\n"
        
        return [TextContent(type="text", text=response)]
    except McpError:
        raise
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=USER_PROFILE_DESCRIPTION.model_dump_json())
async def user_profile(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        _reset_daily_xp_if_needed(user)
        
        # Calculate achievements
        total_quests = len(user.quests_completed)
        climate_quests = len([q for q in user.quests_completed if QUESTS.get(q, {}).get('quest_type') == 'climate'])
        social_quests = len([q for q in user.quests_completed if QUESTS.get(q, {}).get('quest_type') == 'social'])
        personal_quests = len([q for q in user.quests_completed if QUESTS.get(q, {}).get('quest_type') == 'personal'])
        
        # Calculate level (every 50 XP = 1 level)
        level = (user.total_xp // 50) + 1
        xp_to_next = 50 - (user.total_xp % 50)
        
        response = (
            f"👤 **{user.name}'s Profile**\n\n"
            f"🏆 **Level {level}** ({user.total_xp} XP)\n"
            f"📈 **Progress:** {user.total_xp % 50}/50 XP to next level\n\n"
            f"📊 **Stats:**\n"
            f"   • Daily XP: {user.daily_xp}/15 ⚡\n"
            f"   • Total Quests: {total_quests} 🎯\n"
            f"   • Streak: {user.streak_days} days 🔥\n\n"
            f"🎯 **Quest Breakdown:**\n"
            f"   • Climate: {climate_quests} 🌱\n"
            f"   • Social: {social_quests} 🤝\n"
            f"   • Personal: {personal_quests} 📚\n\n"
        )
        
        if user.streak_days >= 7:
            response += f"🔥 **Streak Master!** You've been completing quests for {user.streak_days} days!\n\n"
        
        if xp_to_next < 10:
            response += f"🎯 **Almost there!** Just {xp_to_next} more XP to level up!\n\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=LIST_REWARDS_DESCRIPTION.model_dump_json())
async def list_rewards(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        
        response = "🎁 **Available Rewards**\n\n"
        
        for reward in REWARDS.values():
            is_earned = user.total_xp >= reward.xp_required
            is_claimed = puch_user_id in reward.given_to
            status_emoji = "✅" if is_claimed else "🎯" if is_earned else "🔒"
            type_emoji = {"voucher": "🎫", "tshirt": "👕", "sticker": "🏷️", "badge": "🏆"}[reward.reward_type]
            
            response += (
                f"{status_emoji} **{reward.title}** {type_emoji}\n"
                f"   📊 Required XP: {reward.xp_required}\n"
                f"   🏷️ Type: {reward.reward_type.title()}\n"
            )
            
            if is_claimed:
                response += "   ✅ **Claimed!**\n"
            elif is_earned:
                response += "   🎯 **Ready to claim!**\n"
            else:
                remaining = reward.xp_required - user.total_xp
                response += f"   🔒 **{remaining} XP needed**\n"
            
            response += "\n"
        
        return [TextContent(type="text", text=response)]
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool(description=CLAIM_REWARD_DESCRIPTION.model_dump_json())
async def claim_reward(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    reward_id: Annotated[str, Field(description="Reward ID to claim")],
) -> list[TextContent]:
    try:
        user = _get_user(puch_user_id)
        
        if reward_id not in REWARDS:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Reward {reward_id} not found"))
        
        reward = REWARDS[reward_id]
        
        if user.total_xp < reward.xp_required:
            remaining = reward.xp_required - user.total_xp
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Need {remaining} more XP to claim this reward"))
        
        if puch_user_id in reward.given_to:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Reward already claimed"))
        
        # Claim the reward
        reward.given_to.append(puch_user_id)
        if db:
            db.rewards.update_one({"reward_id": reward.reward_id}, {"$set": {"given_to": reward.given_to}}, upsert=True)
        
        type_emoji = {"voucher": "🎫", "tshirt": "👕", "sticker": "🏷️", "badge": "🏆"}[reward.reward_type]
        
        response = (
            f"🎉 **Reward Claimed Successfully!**\n\n"
            f"{type_emoji} **{reward.title}**\n"
            f"🏷️ **Type:** {reward.reward_type.title()}\n"
            f"📊 **Required XP:** {reward.xp_required}\n\n"
            f"🌟 **Congratulations!** You've earned this reward through your dedication!\n\n"
        )
        
        if reward.reward_type == "voucher":
            response += "💳 **Voucher Code:** QUEST2024-{user.user_id[:8]}\n"
        elif reward.reward_type == "tshirt":
            response += "👕 **T-Shirt Size:** Please contact support with your size preference\n"
        elif reward.reward_type == "sticker":
            response += "🏷️ **Sticker:** Will be mailed to your registered address\n"
        elif reward.reward_type == "badge":
            response += "🏆 **Badge:** Added to your profile! Check your achievements!\n"
        
        return [TextContent(type="text", text=response)]
    except McpError:
        raise
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

# --- Run MCP Server ---
async def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8086"))
    print(f"🎮 Starting Quest & Rewards MCP server on http://{host}:{port}")
    print("🌟 Initializing default quests and rewards...")
    _initialize_default_content()
    print("✅ Default content loaded!")
    print(f"🔗 MCP Endpoint (local): http://localhost:{port}/mcp/")
    print("🌐 Deployed (Render): use your Render URL + '/mcp/'")
    print(f"🔑 Auth Token: {TOKEN}")
    print("🚀 Server is ready! Keep this terminal open.")
    await mcp.run_async("streamable-http", host=host, port=port)

if __name__ == "__main__":
    asyncio.run(main())
