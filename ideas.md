# Project Ideas & Polish

## Visual & Animation Polishes
- [x] **Card Flip Animation**: Add a 3D flip effect when revealing the card or the answer.
- [ ] **Enhanced Card Flip Animations**: 3D card flip effect when revealing answers or transitioning between cards
- [ ] **Particle Effects**: Add subtle particle effects for correct answers (sparkles, confetti) and wrong answers (shake animation, red flash)
- [ ] **Score Counter Animations**: Animate score changes with a count-up effect and scale/pulse animation
- [ ] **Loading Skeleton States**: Replace loading spinners with card-shaped skeleton loaders that better match the final content
- [x] **Confetti Celebration**: Trigger a confetti explosion for high streaks or high scores.
- [x] **Dynamic Backgrounds**: Change the page background color subtly based on the current card's color identity.
- [ ] **Smooth Transitions**: Add page transition effects when navigating between games
- [ ] **Mana Symbol Animation**: Pulse or glow effect when selecting mana symbols
- [ ] **Life Counter Animation**: Heartbeat or fade animation when losing lives

## UX Enhancements
- [ ] **Keyboard Shortcuts**: Add hotkeys for common actions (Enter to submit, numbers for mana symbols, R to restart, Space for next card)
- [x] **Sound Effects**: Add optional sound effects for correct/incorrect guesses and game over (with mute toggle).
- [ ] **Streak Indicators**: Show visual streak indicators (e.g., "🔥 5 streak!") to encourage continued correct guesses
- [ ] **Progress Bars**: Add visual progress indicators for streaks, session stats, or leaderboard proximity
- [ ] **Undo Last Guess**: Allow undoing the last guess (costs a life or reduces score)
- [ ] **Card History Modal**: Click on session history cards to see full details (art, rules text, why you got it right/wrong)
- [ ] **Tutorial/Onboarding**: First-time user walkthrough explaining game mechanics
- [ ] **Color-Blind Mode**: Alternative color schemes and symbols for accessibility
- [ ] **Dark/Light Mode Toggle**: User preference for theme (currently dark by default)
- [ ] **Responsive Card Preview**: Hover/tap on mana symbols to see what they represent

## Gameplay Enhancements
- [x] **Hint System**: Allow users to spend score/streak to get a hint (e.g., reveal 1 color, reveal CMC).
- [ ] **Difficulty Modes**: Easy (common cards only), Normal, Hard (obscure cards, faster timer)
- [ ] **Timed Mode**: Add optional timer for each guess with bonus points for speed
- [ ] **Power/Toughness Higher or Lower**: A variation of the Higher/Lower game using creature stats.
- [ ] **"Sudden Death" Mode**: A game mode with 1 life and increasing difficulty.
- [ ] **Set/Era Filters**: Allow filtering by specific blocks or time periods (e.g., "Pre-Modern", "Recent Sets").
- [ ] **Rarity-Based Difficulty**: Filter by rarity (commons are easier, mythics are harder)
- [ ] **Multiplayer Mode**: Real-time competitive mode where players race to guess correctly
- [ ] **Card Type Filters**: Filter by creature, instant, sorcery, etc.
- [ ] **Commander Format**: Cards from Commander-legal sets only

## Data & Stats
- [ ] **Personal Statistics Page**: Track accuracy by color, set, card type; show improvement over time
- [ ] **Session Recap**: End-of-session summary showing cards guessed, accuracy %, favorite color identity
- [ ] **Achievement System**: Badges for milestones (100 correct guesses, 10-streak, all colors mastered)
- [ ] **Performance Analytics**: Charts showing accuracy trends over time
- [ ] **Card Database Stats**: Show most/least guessed cards, hardest cards
- [ ] **Export Stats**: Download personal statistics as JSON/CSV
- [ ] **Comparison Stats**: Compare your stats to global averages

## Social & Retention
- [x] **Share Result**: Add a "Share" button to copy the score/streak to clipboard for easy sharing on social media.
- [x] **Daily Challenge**: A fixed seed of 5 cards per day so everyone guesses the same ones; leaderboard for the daily challenge.
- [ ] **Enhanced Daily Challenge**: Same card for all players each day with a special leaderboard
- [ ] **Challenge Friends**: Generate custom challenge links with specific cards or filters
- [ ] **Weekly Tournaments**: Competitive weekly events with special rules
- [ ] **User Profiles**: Create accounts to track long-term progress and rankings
- [ ] **Friend Leaderboards**: Compete specifically against friends
- [ ] **Community Highlights**: Featured high scores or perfect games
- [ ] **Shareable Result Cards**: Generate image cards (like Wordle) showing stats without spoilers

## Accessibility & Polish
- [ ] **Screen Reader Support**: Proper ARIA labels and semantic HTML
- [ ] **Reduced Motion Mode**: Respect prefers-reduced-motion for animations
- [ ] **Focus Indicators**: Clear keyboard navigation indicators
- [ ] **Touch Target Optimization**: Ensure all buttons are at least 44x44px
- [ ] **Error Messages**: Clearer, more helpful error messages for network issues
- [ ] **Offline Mode**: Service worker for offline gameplay with cached cards
- [ ] **Multi-language Support**: i18n for international users

## Performance & Technical
- [ ] **Image Optimization**: Lazy load and compress card images
- [ ] **PWA Features**: Installable app with offline support
- [ ] **Analytics Integration**: Google Analytics or Plausible for usage tracking
- [ ] **Rate Limiting**: Proper rate limiting for API endpoints
- [ ] **CDN for Static Assets**: Serve images and CSS from CDN
- [ ] **Caching Strategy**: Aggressive caching for card data
- [ ] **Compression**: Enable gzip/brotli compression for responses

## Monetization (Optional)
- [ ] **Premium Features**: Ad-free experience, exclusive game modes
- [ ] **Donations**: Ko-fi or Patreon link for supporters
- [ ] **Card Affiliate Links**: Referral links to TCGPlayer/Card Kingdom
- [ ] **Cosmetic Upgrades**: Custom themes, card backs, animations
- [ ] **Tournament Entry Fees**: Small fees for special competitive events

## Integration & Expansion
- [ ] **Scryfall API Optimization**: Smart caching, batch requests
- [ ] **Card Set Expansion**: Add more sets as they're released
- [ ] **Other TCGs**: Expand to Pokémon, Yu-Gi-Oh!, etc.
- [ ] **Deckbuilder Integration**: Save cards you like to a deck wishlist
- [ ] **Price Tracking**: Show current card market prices
- [ ] **Ruling Tooltip**: Show Oracle text and rulings on card reveal
- [ ] **Art Credit Display**: Show artist name and appreciation

## Game-Specific Features
- [ ] **"Guess the Artist" Mode**: Show card art, guess the artist (great for art appreciation)
- [ ] **"Flavor Text Challenge"**: Show flavor text, guess the card name
- [ ] **"Release Date Guesser"**: Guess which set/year a card is from
- [ ] **"Power Level Quiz"**: Guess if a card is competitively viable, casual, or jank
- [ ] **"Creature Stats Challenge"**: Guess power/toughness from just the card name
- [ ] **"Color Identity Quiz"**: See card name only, guess its colors
- [ ] **"Planeswalker Edition"**: Dedicated mode for planeswalker cards only

## Meta Features
- [ ] **Card Difficulty Rating**: User-voted difficulty ratings that affect scoring
- [ ] **Adaptive Difficulty**: Algorithm learns from your performance and adjusts card selection
- [ ] **Seasons & Resets**: Quarterly leaderboard resets with seasonal themes
- [ ] **Daily Login Rewards**: Streak bonuses for consecutive days played
- [ ] **Progression System**: Level up by playing, unlock new game modes/features
- [ ] **Battle Pass**: Free and premium tracks with cosmetic rewards
- [ ] **Customizable Scoring**: Let users adjust point values for their preferred challenge

## Community Features
- [ ] **Card Comments**: Let users leave tips or fun facts about specific cards
- [ ] **Vote on Daily Challenges**: Community votes on tomorrow's daily challenge cards
- [ ] **Screenshot Gallery**: Share and browse notable game moments
- [ ] **Featured Players**: Spotlight top players weekly
- [ ] **Guest Curated Challenges**: MTG content creators make custom challenges
- [ ] **Community Tournaments**: Regular community-run competitions
- [ ] **Discussion Forums**: Dedicated space for strategy and card discussion

## Fun Polish
- [ ] **Card Rarity Glow**: Mythics have premium gold glow effect when revealed
- [ ] **Deck-Themed Music**: Background music that shifts based on color identity
- [ ] **Special Events**: Holiday-themed challenges (Halloween horror cards, Christmas snow effects)
- [ ] **Card Lore Tooltips**: Show interesting trivia about cards on reveal
- [ ] **Easter Eggs**: Hidden references to iconic MTG moments
- [ ] **Animated Card Frames**: Premium animated borders for special achievements
- [ ] **Seasonal Themes**: UI changes for different times of year
