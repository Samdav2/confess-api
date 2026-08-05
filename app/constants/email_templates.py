from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class EmailTemplatePreset(BaseModel):
    id: str
    name: str
    category: str  # promotional, informational, marketing, engagement
    subject: str
    preview_text: str
    html_content: str
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None


PREDESIGNED_EMAIL_TEMPLATES: List[EmailTemplatePreset] = [
    EmailTemplatePreset(
        id="promotional",
        name="Promotional Offer & Discount",
        category="promotional",
        subject="Special Confess Offer: Unlock Exclusive Features Today!",
        preview_text="Enjoy special savings on Confess premium secret notes and celebration pages for a limited time.",
        html_content=(
            "<h2>Unleash Your Feelings with Special Savings!</h2>\n"
            "<p>We're thrilled to offer our valued members an exclusive limited-time promotion across all premium features on Confess.</p>\n"
            "<p>Whether you're sending an anonymous secret confession, creating a customized celebration page, or unlocking custom themes, now is the perfect time to explore!</p>\n"
            "<ul>\n"
            "  <li><strong>20% Off</strong> Premium Celebration Pages</li>\n"
            "  <li><strong>Priority Delivery</strong> for Confession Messages</li>\n"
            "  <li><strong>Custom Styling & Music Options</strong></li>\n"
            "</ul>\n"
            "<p>Don't miss out on making someone's day extra memorable.</p>"
        ),
        cta_text="Claim Your Offer Now",
        cta_link="https://confess.com.ng/promotions",
    ),
    EmailTemplatePreset(
        id="informational",
        name="Important Platform Announcement",
        category="informational",
        subject="Important Update: Exciting Enhancements Coming to Confess",
        preview_text="Read about major improvements, enhanced privacy tools, and new features designed for you.",
        html_content=(
            "<h2>Exciting Platform Updates & Improvements</h2>\n"
            "<p>At Confess, we are continuously striving to deliver the best, safest, and most delighting experience for our community.</p>\n"
            "<p>We are excited to announce several major enhancements currently rolling out:</p>\n"
            "<p><strong>1. Enhanced Privacy Controls:</strong> Upgraded encryption and security standards to keep your confessions completely private and safe.</p>\n"
            "<p><strong>2. Faster Real-Time Notifications:</strong> Instant delivery alerts when your messages are opened or responded to.</p>\n"
            "<p><strong>3. Refined Mobile Experience:</strong> A smoother, faster interface across all mobile browsers.</p>\n"
            "<p>Thank you for being an integral part of the Confess community!</p>"
        ),
        cta_text="Explore What's New",
        cta_link="https://confess.com.ng/announcements",
    ),
    EmailTemplatePreset(
        id="newsletter",
        name="Confess Community Digest",
        category="marketing",
        subject="The Confess Digest: Trending Confessions & Top Highlights",
        preview_text="Catch up on the most touching stories, community highlights, and secret trends of the week.",
        html_content=(
            "<h2>Welcome to The Confess Digest!</h2>\n"
            "<p>Here is your weekly round-up of heartfelt stories, trending topics, and community highlights from the Confess ecosystem.</p>\n"
            "<div style=\"background: #fafafa; padding: 16px; border-radius: 6px; margin: 16px 0;\">\n"
            "  <h3 style=\"margin-top: 0; color: #dc2626;\">Highlight of the Week</h3>\n"
            "  <p><em>\"Over 10,000 secret confessions and celebration cards were delivered across Nigeria this week alone!\"</em></p>\n"
            "</div>\n"
            "<p>Check out our latest blog articles and community features to stay inspired.</p>"
        ),
        cta_text="Read Full Digest",
        cta_link="https://confess.com.ng/blog",
    ),
    EmailTemplatePreset(
        id="event_invitation",
        name="Special Event & Gathering Invitation",
        category="engagement",
        subject="You're Invited: Exclusive Confess Live Session!",
        preview_text="Join us for a virtual interactive session celebrating anonymous expressions and heartfelt stories.",
        html_content=(
            "<h2>Join Us for an Exclusive Confess Event!</h2>\n"
            "<p>You are cordially invited to our upcoming virtual community event: <strong>Confess Unfiltered & Live</strong>.</p>\n"
            "<p><strong>Date & Time:</strong> Upcoming Saturday at 6:00 PM WAT<br>\n"
            "<strong>Location:</strong> Online (Virtual Stage)</p>\n"
            "<p>Expect inspiring story breakdowns, secret reveals, Q&A with our team, and live giveaway prizes!</p>\n"
            "<p>Spaces are limited, so make sure to reserve your spot today.</p>"
        ),
        cta_text="Reserve Your Spot",
        cta_link="https://confess.com.ng/events",
    ),
    EmailTemplatePreset(
        id="product_update",
        name="New Feature & Product Release",
        category="informational",
        subject="New Feature Alert: Custom Celebration Pages & Audio Notes!",
        preview_text="Discover our newest tools to express love, friendship, and secret thoughts like never before.",
        html_content=(
            "<h2>Introducing New Ways to Express Yourself!</h2>\n"
            "<p>We are thrilled to release our latest feature updates designed to give your confessions and celebrations a personal touch:</p>\n"
            "<p>✨ <strong>Audio Voice Notes:</strong> Attach short voice clips to your confession cards.<br>\n"
            "🎉 <strong>Interactive Celebration Pages:</strong> Craft rich celebration landing pages for birthdays, anniversaries, and milestones.<br>\n"
            "💌 <strong>Custom Themes & Animations:</strong> Choose vibrant confetti, heart animations, and smooth transitions.</p>\n"
            "<p>Try out these new tools right now on your account dashboard!</p>"
        ),
        cta_text="Try New Features",
        cta_link="https://confess.com.ng/dashboard",
    ),
    EmailTemplatePreset(
        id="reengagement",
        name="User Re-engagement / We Miss You",
        category="engagement",
        subject="We Miss You on Confess! Here's a Special Surprise",
        preview_text="It's been a while since your last visit. See what's new and claim a free secret key inside.",
        html_content=(
            "<h2>We've Missed Having You Around!</h2>\n"
            "<p>Hi there! We noticed it's been a little while since you last checked in on Confess.</p>\n"
            "<p>Our platform has gotten faster, sleeker, and full of exciting new ways to send anonymous notes and celebrate your loved ones.</p>\n"
            "<p>To welcome you back, we've credited a free premium feature unlock to your account for your next message.</p>\n"
            "<p>Come back in and see who might be waiting to hear from you!</p>"
        ),
        cta_text="Return to Confess",
        cta_link="https://confess.com.ng/login",
    ),
    EmailTemplatePreset(
        id="feedback_request",
        name="User Feedback & Community Survey",
        category="informational",
        subject="We Value Your Voice: How Can We Improve Confess?",
        preview_text="Take 2 minutes to share your feedback and help us build a better platform for everyone.",
        html_content=(
            "<h2>Your Opinion Matters to Us</h2>\n"
            "<p>Hello! As a member of our community, your experience on Confess is our top priority.</p>\n"
            "<p>We'd love to know what features you enjoy most and where we can make things even better for you.</p>\n"
            "<p>Could you spare 2 minutes to complete our short, anonymous feedback survey?</p>\n"
            "<p>Your insights directly shape our roadmap and upcoming releases.</p>"
        ),
        cta_text="Share Your Feedback",
        cta_link="https://confess.com.ng/feedback",
    ),
    EmailTemplatePreset(
        id="seasonal",
        name="Seasonal / Holiday Special Campaign",
        category="promotional",
        subject="Celebrate the Season of Love & Secrets with Confess",
        preview_text="Send special holiday confessions and personalized greetings to your favorite people today.",
        html_content=(
            "<h2>Celebrate the Season with Confess!</h2>\n"
            "<p>The holiday season is all about love, appreciation, and unforgettable moments.</p>\n"
            "<p>Whether you want to express feelings you've held back all year or send a heartwarming secret card to a friend, Confess makes it magical and effortless.</p>\n"
            "<p>Explore our exclusive holiday-themed designs and spread joy today!</p>"
        ),
        cta_text="Send a Holiday Card",
        cta_link="https://confess.com.ng/create",
    ),
    EmailTemplatePreset(
        id="welcome_onboarding",
        name="New Member Onboarding Guide",
        category="marketing",
        subject="Welcome to Confess: Your Quick Guide to Getting Started",
        preview_text="Learn how to send your first anonymous confession or create custom celebration links in 3 easy steps.",
        html_content=(
            "<h2>Welcome to Confess!</h2>\n"
            "<p>We are delighted to have you join our platform. Confess is built to help you express your innermost feelings, secrets, and celebrations safely and beautifully.</p>\n"
            "<h3>3 Quick Steps to Get Started:</h3>\n"
            "<ol>\n"
            "  <li><strong>Create a Confession Link:</strong> Generate your unique link and share it on social media.</li>\n"
            "  <li><strong>Send Secret Messages:</strong> Express anonymous thoughts or send custom celebration cards to friends.</li>\n"
            "  <li><strong>Track Responses:</strong> Get notified instantly when someone reads or replies to your note.</li>\n"
            "</ol>\n"
            "<p>Ready to make your first confession or celebration page?</p>"
        ),
        cta_text="Get Started Now",
        cta_link="https://confess.com.ng/start",
    ),
    EmailTemplatePreset(
        id="targeted_exclusive",
        name="VIP Exclusive Perks & Access",
        category="promotional",
        subject="VIP Access: You've Been Selected for Exclusive Confess Perks!",
        preview_text="Enjoy early access to new secret tools, priority support, and custom themes as a VIP member.",
        html_content=(
            "<h2>Exclusive VIP Perks Just for You</h2>\n"
            "<p>As one of our most active and valued community members, you've unlocked <strong>VIP Member Status</strong> on Confess!</p>\n"
            "<p>Here is what your VIP status unlocks:</p>\n"
            "<ul>\n"
            "  <li><strong>Early Access:</strong> Test brand new features before general release.</li>\n"
            "  <li><strong>Exclusive Themes:</strong> Access VIP-only animated backgrounds & sound effects.</li>\n"
            "  <li><strong>Priority Support:</strong> Direct assistance from our dedicated team whenever needed.</li>\n"
            "</ul>\n"
            "<p>Click below to activate your VIP perks on your profile immediately.</p>"
        ),
        cta_text="Activate VIP Perks",
        cta_link="https://confess.com.ng/vip",
    ),
]


def get_all_templates() -> List[EmailTemplatePreset]:
    return PREDESIGNED_EMAIL_TEMPLATES


def get_template_by_id(template_id: str) -> Optional[EmailTemplatePreset]:
    for t in PREDESIGNED_EMAIL_TEMPLATES:
        if t.id == template_id:
            return t
    return None
