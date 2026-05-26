# backend/verticals/receptionist/receptionist_agent.py
"""
AI Receptionist Agent (Feature 13).

24/7 multilingual reception with:
  1. Twilio Voice — inbound call handling with TwiML
  2. WhatsApp Business — via existing Twilio WhatsApp integration
  3. Embeddable JS Widget — served as static HTML/JS snippet
  4. Intent classification: appointment | inquiry | complaint | transfer_to_human
  5. Calendly booking integration
  6. Human transfer via HITL when needed

Language: auto-detects English, Hindi, Tamil from message content.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Intents ──────────────────────────────────────────────────────────────────

_INTENT_KEYWORDS = {
    "appointment":   ["appointment", "schedule", "book", "meeting", "call", "slot",
                      "मिलना", "मीटिंग", "சந்திப்பு", "நேரம்"],
    "inquiry":       ["price", "cost", "information", "details", "know", "what",
                      "कीमत", "जानकारी", "விலை", "தகவல்"],
    "complaint":     ["problem", "issue", "complaint", "not working", "broken", "bad",
                      "शिकायत", "समस्या", "புகார்"],
    "human":         ["human", "agent", "person", "transfer", "speak to someone",
                      "मनुष्य", "इंसान", "மனிதர்"],
    "hours":         ["hours", "timing", "open", "close", "when",
                      "समय", "நேரம்"],
    "location":      ["address", "location", "where", "directions",
                      "पता", "முகவரி"],
}


def classify_intent(message: str) -> str:
    """Returns: appointment | inquiry | complaint | human | hours | location | general"""
    m = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in m for kw in keywords):
            return intent
    return "general"


# ── Response templates ────────────────────────────────────────────────────────

_GREETINGS = {
    "en": "Hello! I'm your AI receptionist. How can I assist you today?",
    "hi": "नमस्ते! मैं आपका AI receptionist हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
    "ta": "வணக்கம்! நான் உங்கள் AI receptionist. இன்று உங்களுக்கு எப்படி உதவலாம்?",
}

_OFFICE_HOURS = {
    "en": "Our office is open Monday to Friday, 9 AM to 6 PM IST. Saturdays 10 AM to 2 PM.",
    "hi": "हमारा कार्यालय सोमवार से शुक्रवार, सुबह 9 बजे से शाम 6 बजे IST तक खुला है।",
    "ta": "எங்கள் அலுவலகம் திங்கள் முதல் வெள்ளி வரை, காலை 9 மணி முதல் மாலை 6 மணி வரை திறந்திருக்கும்.",
}


def _detect_language(text: str) -> str:
    if any(c in text for c in "अआइईउऊएओ"):
        return "hi"
    if any(c in text for c in "அஆஇஈஉஊ"):
        return "ta"
    return "en"


async def handle_receptionist_message(
    message:       str,
    channel:       str = "web",    # web | whatsapp | voice
    session_id:    str = "",
    user_name:     Optional[str] = None,
) -> dict:
    """
    Process incoming receptionist message and return structured response.

    Args:
        message:    Incoming text from user
        channel:    Originating channel (web widget, WhatsApp, or voice)
        session_id: Conversation session ID
        user_name:  Optional name from WhatsApp/voice metadata

    Returns:
        dict with response text, intent, suggested_actions, transfer_needed
    """
    language = _detect_language(message)
    intent   = classify_intent(message)

    name_part = f" {user_name}" if user_name else ""
    response  = ""
    actions: list[dict] = []
    transfer  = False

    if intent == "appointment":
        response = {
            "en": f"I'd be happy to schedule an appointment{name_part}! Please tell me your preferred date and time, and I'll check availability.",
            "hi": f"मुझे{name_part} appointment schedule करने में खुशी होगी! कृपया अपनी पसंदीदा तारीख और समय बताएं।",
            "ta": f"சந்திப்பு திட்டமிட மகிழ்ச்சியாக இருக்கிறேன்{name_part}! உங்கள் விருப்பமான தேதி மற்றும் நேரத்தை சொல்லுங்கள்.",
        }[language]
        actions = [
            {"type": "calendly_link", "label": "Book a slot", "url": "https://calendly.com/your-org"},
        ]

    elif intent == "inquiry":
        response = {
            "en": "I'll be happy to help with your inquiry. What specifically would you like to know about?",
            "hi": "मुझे आपकी जानकारी देने में खुशी होगी। आप किस बारे में जानना चाहते हैं?",
            "ta": "உங்கள் கேள்விக்கு உதவ மகிழ்ச்சியாக இருக்கிறேன். என்ன தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
        }[language]

    elif intent == "complaint":
        response = {
            "en": "I'm sorry to hear you're experiencing an issue. I'm connecting you with a support specialist right away.",
            "hi": "मुझे खेद है कि आपको समस्या हो रही है। मैं आपको तुरंत एक support specialist से जोड़ रहा हूँ।",
            "ta": "உங்களுக்கு சிக்கல் இருப்பதை கேட்டு வருந்துகிறேன். உடனடியாக support specialist-ஐ இணைக்கிறேன்.",
        }[language]
        transfer = True

    elif intent == "human":
        response = {
            "en": "Of course! Let me transfer you to one of our team members.",
            "hi": "बिल्कुल! मैं आपको हमारे team members में से एक के पास transfer कर रहा हूँ।",
            "ta": "நிச்சயமாக! எங்கள் team member-ஐ இணைக்கிறேன்.",
        }[language]
        transfer = True

    elif intent == "hours":
        response = _OFFICE_HOURS[language]

    elif intent == "location":
        response = {
            "en": "Our office is located at: 123 AI Street, Chennai, Tamil Nadu 600001. Google Maps: https://maps.google.com",
            "hi": "हमारा कार्यालय: 123 AI Street, Chennai, Tamil Nadu 600001 पर स्थित है।",
            "ta": "எங்கள் அலுவலகம்: 123 AI Street, Chennai, Tamil Nadu 600001.",
        }[language]

    else:
        # General query → LLM (Ollama-first)
        try:
            from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
            response = await ollama_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a friendly, professional AI receptionist. "
                            f"Respond in {language}. Be concise (2-3 sentences max). "
                            f"If you don't know the answer, offer to connect with a human agent."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                model=OLLAMA_MODEL,
                max_tokens=200,
            )
            if not response:
                response = _GREETINGS[language]
        except Exception:
            response = _GREETINGS[language]

    return {
        "response":          response,
        "intent":            intent,
        "language":          language,
        "channel":           channel,
        "transfer_to_human": transfer,
        "suggested_actions": actions,
        "session_id":        session_id,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
    }


# ── Twilio TwiML helpers ─────────────────────────────────────────────────────

def build_voice_twiml(message: str, language: str = "en") -> str:
    """Generate TwiML XML for Twilio voice response."""
    # Language to Twilio voice mapping
    voice_map = {
        "en": "Polly.Amy",
        "hi": "Polly.Aditi",
        "ta": "Polly.Raveena",
    }
    voice = voice_map.get(language, "Polly.Amy")

    # XML-escape message to prevent TwiML injection (e.g. if message contains & or <)
    import xml.sax.saxutils as saxutils
    safe_message = saxutils.escape(message)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{safe_message}</Say>
    <Gather input="speech" action="/api/verticals/receptionist/voice-response" method="POST" language="{language}">
        <Say voice="{voice}">How can I help you today?</Say>
    </Gather>
</Response>"""


def build_inbound_twiml(language: str = "en") -> str:
    """TwiML for inbound call greeting."""
    greeting = _GREETINGS.get(language, _GREETINGS["en"])
    return build_voice_twiml(greeting, language)


# ── Embeddable widget HTML ────────────────────────────────────────────────────

def get_widget_embed_code(
    api_url:     str,
    theme_color: str = "#534AB7",
    greeting:    str = "Hi! How can I help you?",
) -> str:
    """
    Return embeddable JavaScript widget HTML snippet.
    Customers paste this into their website's <body> tag.
    """
    return f"""<!-- AI Receptionist Widget — paste before </body> -->
<div id="ai-receptionist-widget"></div>
<script>
(function() {{
  var API_URL = '{api_url}/api/receptionist/chat';
  var THEME   = '{theme_color}';
  var GREETING= '{greeting}';

  var style = document.createElement('style');
  style.textContent = `
    #ai-chat-bubble {{
      position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    }}
    #ai-chat-toggle {{
      width: 56px; height: 56px; border-radius: 50%; background: {theme_color};
      border: none; cursor: pointer; color: white; font-size: 24px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2); display: flex;
      align-items: center; justify-content: center;
    }}
    #ai-chat-window {{
      display: none; position: fixed; bottom: 96px; right: 24px;
      width: 360px; height: 480px; background: white; border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.15); flex-direction: column;
      overflow: hidden; font-family: sans-serif;
    }}
    #ai-chat-window.open {{ display: flex; }}
    #ai-chat-header {{
      background: {theme_color}; color: white; padding: 16px;
      font-weight: 600; font-size: 15px;
    }}
    #ai-chat-messages {{
      flex: 1; overflow-y: auto; padding: 16px; display: flex;
      flex-direction: column; gap: 8px;
    }}
    .ai-msg, .user-msg {{
      padding: 10px 14px; border-radius: 12px; max-width: 80%; font-size: 13px;
    }}
    .ai-msg {{ background: #f3f4f6; align-self: flex-start; color: #111; }}
    .user-msg {{ background: {theme_color}; color: white; align-self: flex-end; }}
    #ai-chat-input-row {{
      display: flex; padding: 12px; border-top: 1px solid #e5e7eb; gap: 8px;
    }}
    #ai-chat-input {{
      flex: 1; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 12px;
      font-size: 13px; outline: none;
    }}
    #ai-chat-send {{
      background: {theme_color}; color: white; border: none; border-radius: 8px;
      padding: 8px 14px; cursor: pointer; font-size: 13px;
    }}
  `;
  document.head.appendChild(style);

  var html = '<div id="ai-chat-bubble">' +
    '<button id="ai-chat-toggle" onclick="toggleChat()">💬</button>' +
    '</div>' +
    '<div id="ai-chat-window">' +
      '<div id="ai-chat-header">🤖 AI Assistant</div>' +
      '<div id="ai-chat-messages"><div class="ai-msg">' + GREETING + '</div></div>' +
      '<div id="ai-chat-input-row">' +
        '<input id="ai-chat-input" type="text" placeholder="Type a message..." ' +
               'onkeydown="if(event.key===\'Enter\')sendMsg()" />' +
        '<button id="ai-chat-send" onclick="sendMsg()">Send</button>' +
      '</div>' +
    '</div>';
  document.getElementById('ai-receptionist-widget').innerHTML = html;

  window.toggleChat = function() {{
    document.getElementById('ai-chat-window').classList.toggle('open');
  }};

  var sessionId = 'sess_' + Math.random().toString(36).slice(2, 10);
  window.sendMsg = async function() {{
    var input = document.getElementById('ai-chat-input');
    var msg   = input.value.trim();
    if (!msg) return;
    input.value = '';
    var msgs = document.getElementById('ai-chat-messages');
    msgs.innerHTML += '<div class="user-msg">' + msg + '</div>';
    try {{
      var resp = await fetch(API_URL, {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{message: msg, channel: 'web', session_id: sessionId}})
      }});
      var data = await resp.json();
      msgs.innerHTML += '<div class="ai-msg">' + (data.response || 'Sorry, unable to respond.') + '</div>';
    }} catch(e) {{
      msgs.innerHTML += '<div class="ai-msg">Sorry, connection issue. Please try again.</div>';
    }}
    msgs.scrollTop = msgs.scrollHeight;
  }};
}})();
</script>
<!-- End AI Receptionist Widget -->"""
