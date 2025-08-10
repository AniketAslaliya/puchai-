# Quest & Rewards MCP Server for Puch AI

A gamified quest and rewards system that turns everyday challenges into exciting adventures! Complete quests, earn XP, build streaks, and unlock amazing rewards.

## 🌟 What is This?

This MCP (Model Context Protocol) server creates a fun, gamified experience where users can:
- **Complete Quests** - Take on climate, social, and personal challenges
- **Earn XP** - Gain experience points with daily limits and streak bonuses
- **Unlock Rewards** - Claim vouchers, t-shirts, stickers, and badges
- **Build Streaks** - Maintain daily quest completion for bonus rewards
- **Create Custom Quests** - Design your own challenges for personal goals

## 🎮 Features

### Quest Types
- **🌱 Climate Quests** - Environmental challenges (plant trees, reduce plastic)
- **🤝 Social Quests** - Community and helping others
- **📚 Personal Quests** - Self-improvement and learning goals

### XP & Rewards System
- **Daily XP Limit** - Maximum 15 XP per day
- **Streak Bonuses** - Extra XP for daily quest completion
- **Golden Quests** - Double XP special challenges
- **Milestone Rewards** - Unlock rewards at XP thresholds

### Fun Elements
- **Emoji-rich responses** - Every interaction is gamified
- **Playful onboarding** - Welcome new adventurers with style
- **Progress tracking** - Level system and achievement badges
- **Social sharing** - Share quest IDs with friends

## 🚀 Quick Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
uv venv

# Install all required packages
uv sync

# Activate the environment
source .venv/bin/activate
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```env
AUTH_TOKEN=your_secret_token_here
MY_NUMBER=918320382391
```

### Step 3: Run the Quest Server

```bash
cd mcp-bearer-token
python quest_rewards_mcp.py
```

You'll see: `🎮 Starting Quest & Rewards MCP server on http://0.0.0.0:8086`

### Step 4: Make It Public (Required by Puch)

#### Option A: Using ngrok (Recommended)

1. **Install ngrok:**
   Download from https://ngrok.com/download

2. **Get your authtoken:**
   - Go to https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your authtoken
   - Run: `ngrok config add-authtoken YOUR_AUTHTOKEN`

3. **Start the tunnel:**
   ```bash
   ngrok http 8086
   ```

#### Option B: Deploy to Cloud

Deploy to services like:
- Railway
- Render
- Heroku
- DigitalOcean App Platform

## 🔗 Connect with Puch AI

1. **[Open Puch AI](https://wa.me/+919998881729)** in your browser
2. **Start a new conversation**
3. **Use the connect command:**
   ```
   /mcp connect https://your-domain.ngrok.app/mcp your_secret_token_here
   ```

## 🎯 Available Tools

### User Management
- **`register_user`** - Start your quest journey with fun onboarding
- **`user_profile`** - View your stats, level, and achievements

### Quest System
- **`create_quest`** - Create custom quests (personal or for others)
- **`list_quests`** - Browse available challenges with filters
- **`complete_quest`** - Finish quests and earn XP

### Rewards System
- **`list_rewards`** - See available rewards and your progress
- **`claim_reward`** - Unlock rewards you've earned

## 📊 Data Models

### User
```json
{
  "user_id": "string",
  "name": "string", 
  "total_xp": 0,
  "daily_xp": 0,
  "quests_completed": [],
  "streak_days": 0,
  "created_at": "datetime"
}
```

### Quest
```json
{
  "quest_id": "string",
  "title": "string",
  "description": "string", 
  "xp_reward": 5,
  "quest_type": "climate|social|personal",
  "is_golden": false,
  "created_by": "string",
  "created_at": "datetime"
}
```

### Reward
```json
{
  "reward_id": "string",
  "title": "string",
  "xp_required": 25,
  "reward_type": "voucher|tshirt|sticker|badge",
  "given_to": [],
  "created_at": "datetime"
}
```

## 🎮 Example Usage

### Starting Your Journey
```
"Hi! I want to start questing!"
```
→ Registers you and shows welcome message

### Creating a Quest
```
"Create a quest to study for 2 hours"
```
→ Creates personal quest with 4 XP reward

### Completing Quests
```
"Complete the plant_tree quest"
```
→ Awards XP and shows progress

### Checking Progress
```
"Show my profile"
```
→ Displays level, XP, streak, and achievements

## 🌟 Default Content

### Pre-loaded Quests
- 🌱 Plant a Tree (5 XP)
- ♻️ Reduce Plastic Use (3 XP) 
- 📱 Recycle Electronics (4 XP)
- 🤝 Help a Neighbor (3 XP)
- 📚 Study for 2 Hours (4 XP)

### Available Rewards
- 🎯 First Quest Badge (0 XP)
- 🌍 Eco Warrior Sticker (25 XP)
- 🔥 Streak Master T-Shirt (100 XP)
- 🏆 XP Champion Voucher (500 XP)

## 🔧 Technical Details

### XP System Rules
- **Daily Limit**: 15 XP maximum per day
- **Streak Bonus**: +1 XP per 7 days of streak (max +3)
- **Golden Quests**: Double XP rewards
- **Level System**: Every 50 XP = 1 level

### Authentication
- Uses Bearer token authentication
- Each user gets unique `puch_user_id`
- No external API keys required

### Storage
- In-memory storage (replace with database for production)
- Data persists during server runtime
- User data scoped by `puch_user_id`

## 🎨 Customization

### Adding New Quest Types
1. Modify the `quest_type` Literal in Quest model
2. Add corresponding emoji in `list_quests` function
3. Update quest creation validation

### Creating New Rewards
1. Add reward to `_initialize_default_content()`
2. Set appropriate XP threshold
3. Choose reward type and title

### Modifying XP Rules
1. Adjust daily limit in `_calculate_xp_gain()`
2. Modify streak bonus calculation
3. Update level system in `user_profile()`

## 🐛 Debug Mode

To get detailed error messages:

```
/mcp diagnostics-level debug
```

## 📚 Additional Resources

### Official Puch AI Documentation
- **Main Documentation**: https://puch.ai/mcp
- **Protocol Compatibility**: Core MCP specification with Bearer support
- **Command Reference**: Complete MCP command documentation

### Technical Specifications
- **JSON-RPC 2.0**: https://www.jsonrpc.org/specification
- **MCP Protocol**: Core protocol messages and tool definitions

## 🤝 Getting Help

- **Join Puch AI Discord:** https://discord.gg/VMCnMvYx
- **Check Puch AI MCP docs:** https://puch.ai/mcp
- **Puch WhatsApp Number:** +91 99988 81729

---

**Happy Questing! 🎮⚔️**

Use the hashtag `#BuildWithPuch` in your posts about your MCP!

Transform everyday challenges into epic adventures with this gamified quest system! 🌟
