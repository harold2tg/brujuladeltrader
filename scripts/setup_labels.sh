#!/bin/bash
# Setup GitHub labels for La Brújula del Trader
# Usage: ./scripts/setup_labels.sh
# Requires: gh CLI authenticated (gh auth login)

set -e

echo "🧭 Setting up GitHub labels for La Brújula del Trader..."

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
  echo "❌ Error: gh CLI not authenticated. Run 'gh auth login' first."
  exit 1
fi

# Color palette
RED="d73a4a"
ORANGE="fb8500"
YELLOW="ffd60a"
GREEN="2ea043"
BLUE="0969da"
PURPLE="8b5cf6"
GRAY="6e7781"

# Type labels
echo "📋 Creating type labels..."
gh label create "bug" --color "$RED" --description "Something isn't working" 2>/dev/null || true
gh label create "enhancement" --color "$GREEN" --description "New feature or request" 2>/dev/null || true
gh label create "documentation" --color "$BLUE" --description "Improvements or additions to documentation" 2>/dev/null || true
gh label create "question" --color "$PURPLE" --description "Further information is requested" 2>/dev/null || true

# Severity labels
echo "🔥 Creating severity labels..."
gh label create "severity:critical" --color "$RED" --description "🔴 Critical — App unusable / cannot trade" 2>/dev/null || true
gh label create "severity:high" --color "$ORANGE" --description "🟠 High — Feature broken, no workaround" 2>/dev/null || true
gh label create "severity:medium" --color "$YELLOW" --description "🟡 Medium — Feature broken, workaround exists" 2>/dev/null || true
gh label create "severity:low" --color "$GREEN" --description "🟢 Low — Cosmetic / minor annoyance" 2>/dev/null || true

# Platform labels
echo "📱 Creating platform labels..."
gh label create "platform:web" --color "$BLUE" --description "Web application" 2>/dev/null || true
gh label create "platform:ios" --color "000000" --description "iOS mobile app" 2>/dev/null || true
gh label create "platform:android" --color "3ddc84" --description "Android mobile app" 2>/dev/null || true
gh label create "platform:api" --color "6f42c1" --description "Backend API" 2>/dev/null || true

# Area labels
echo "🎯 Creating area labels..."
gh label create "area:chart" --color "00758f" --description "Chart and analysis features" 2>/dev/null || true
gh label create "area:ai" --color "ff6b6b" --description "AI assistant features" 2>/dev/null || true
gh label create "area:alerts" --color "ffa500" --description "Alerts and notifications" 2>/dev/null || true
gh label create "area:journal" --color "4ecdc4" --description "Journal and notes" 2>/dev/null || true
gh label create "area:account" --color "95a5a6" --description "Account and billing" 2>/dev/null || true
gh label create "area:auth" --color "e74c3c" --description "Authentication and authorization" 2>/dev/null || true
gh label create "area:payments" --color "27ae60" --description "Payments and subscriptions" 2>/dev/null || true
gh label create "area:ctrader" --color "2980b9" --description "cTrader integration" 2>/dev/null || true

# Status labels
echo "📊 Creating status labels..."
gh label create "status:triage" --color "$GRAY" --description "Needs initial review" 2>/dev/null || true
gh label create "status:confirmed" --color "$BLUE" --description "Bug confirmed, needs fix" 2>/dev/null || true
gh label create "status:in-progress" --color "$ORANGE" --description "Currently being worked on" 2>/dev/null || true
gh label create "status:needs-info" --color "$YELLOW" --description "Waiting for more information" 2>/dev/null || true

# Priority labels (for feature requests)
echo "⭐ Creating priority labels..."
gh label create "priority:must-have" --color "$RED" --description "🔴 Must have — Critical for launch" 2>/dev/null || true
gh label create "priority:important" --color "$ORANGE" --description "🟠 Important — High value" 2>/dev/null || true
gh label create "priority:nice-to-have" --color "$YELLOW" --description "🟡 Nice to have — Medium value" 2>/dev/null || true
gh label create "priority:optional" --color "$GREEN" --description "🟢 Optional — Low priority" 2>/dev/null || true

echo ""
echo "✅ Labels created successfully!"
echo ""
echo "📋 Label summary:"
echo "   Type: bug, enhancement, documentation, question"
echo "   Severity: severity:critical, severity:high, severity:medium, severity:low"
echo "   Platform: platform:web, platform:ios, platform:android, platform:api"
echo "   Area: area:chart, area:ai, area:alerts, area:journal, area:account, area:auth, area:payments, area:ctrader"
echo "   Status: status:triage, status:confirmed, status:in-progress, status:needs-info"
echo "   Priority: priority:must-have, priority:important, priority:nice-to-have, priority:optional"
echo ""
echo "💡 Tip: You can now use these labels in your issue templates!"
