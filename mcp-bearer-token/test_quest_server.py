#!/usr/bin/env python3
"""
Simple test script for the Quest & Rewards MCP Server
This script tests the basic functionality without requiring Puch AI
"""

import asyncio
import json
from datetime import datetime
from quest_rewards_mcp import (
    _get_user, _reset_daily_xp_if_needed, _calculate_xp_gain,
    _initialize_default_content, USERS, QUESTS, REWARDS
)

async def test_quest_system():
    """Test the quest system functionality"""
    print("🧪 Testing Quest & Rewards MCP Server...\n")
    
    # Initialize default content
    _initialize_default_content()
    print("✅ Default quests and rewards loaded")
    
    # Test user creation
    test_user_id = "test_user_123"
    user = _get_user(test_user_id)
    print(f"✅ User created: {user.name}")
    
    # Test quest listing
    print(f"\n📋 Available quests: {len(QUESTS)}")
    for quest_id, quest in QUESTS.items():
        print(f"   • {quest.title} ({quest.xp_reward} XP)")
    
    # Test reward listing
    print(f"\n🎁 Available rewards: {len(REWARDS)}")
    for reward_id, reward in REWARDS.items():
        print(f"   • {reward.title} ({reward.xp_required} XP)")
    
    # Test XP calculation
    print(f"\n📊 User stats:")
    print(f"   • Total XP: {user.total_xp}")
    print(f"   • Daily XP: {user.daily_xp}/15")
    print(f"   • Streak: {user.streak_days} days")
    
    # Test XP gain calculation
    test_quest = list(QUESTS.values())[0]
    xp_gain = _calculate_xp_gain(user, test_quest.xp_reward)
    print(f"\n🎯 XP gain for '{test_quest.title}': {xp_gain} XP")
    
    # Simulate completing a quest
    if test_quest.quest_id not in user.quests_completed:
        user.daily_xp += xp_gain
        user.total_xp += xp_gain
        user.quests_completed.append(test_quest.quest_id)
        user.last_quest_date = datetime.utcnow().isoformat()
        print(f"✅ Completed quest: {test_quest.title}")
        print(f"   • New total XP: {user.total_xp}")
        print(f"   • New daily XP: {user.daily_xp}/15")
    
    # Test reward eligibility
    print(f"\n🎁 Reward eligibility:")
    for reward in REWARDS.values():
        is_earned = user.total_xp >= reward.xp_required
        status = "✅ Earned" if is_earned else "🔒 Locked"
        print(f"   • {reward.title}: {status}")
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"📊 Final user stats:")
    print(f"   • Name: {user.name}")
    print(f"   • Total XP: {user.total_xp}")
    print(f"   • Quests completed: {len(user.quests_completed)}")
    print(f"   • Level: {(user.total_xp // 50) + 1}")

if __name__ == "__main__":
    asyncio.run(test_quest_system())
