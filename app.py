import streamlit as st
import anthropic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Customer Support",
    page_icon="🎧",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .support-header {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .support-header h2 { margin: 0; font-size: 1.4rem; }
    .support-header p  { margin: 0.2rem 0 0; font-size: 0.85rem; opacity: 0.85; }
    .status-badge {
        display: inline-block;
        background: #00c853;
        color: white;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Configuration")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at https://console.anthropic.com",
    )

    st.divider()
    st.markdown("### 🏢 Company Info")

    company_name = st.text_input("Company Name", value="Acme Corp")
    support_topics = st.text_area(
        "What can the bot help with?",
        value="Orders, returns, shipping, product questions, billing",
        height=80,
    )
    escalation_email = st.text_input("Escalation Email", value="support@acmecorp.com")

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.ticket_id = None
        st.rerun()

    st.caption("Powered by [Claude](https://anthropic.com)")

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "ticket_id" not in st.session_state:
    import random, string
    st.session_state.ticket_id = "TKT-" + "".join(random.choices(string.digits, k=6))

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are a friendly and professional customer support agent for {company_name}.

Your responsibilities:
- Help customers with: {support_topics}
- Always greet the customer warmly on the first message
- Be empathetic, patient, and solution-focused
- Ask clarifying questions when needed
- If an issue cannot be resolved through chat, politely direct the customer to email {escalation_email}
- Never make up information — if you don't know something, say so honestly
- Keep responses concise and easy to read (use bullet points where appropriate)
- Always end with asking if there's anything else you can help with

Ticket ID for this session: {st.session_state.ticket_id}
Reference this ticket ID if the customer needs to follow up via email.
"""

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="support-header">
    <h2>🎧 {company_name} — Customer Support</h2>
    <p>We're here to help! Ticket: <strong>{st.session_state.ticket_id}</strong></p>
    <span class="status-badge">● Online</span>
</div>
""", unsafe_allow_html=True)

# ── Welcome message (shown only at start) ─────────────────────────────────────
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🎧"):
        st.markdown(
            f"👋 Hi there! Welcome to **{company_name}** support. "
            f"I'm here to help you with {support_topics.lower()}. "
            f"What can I assist you with today?\n\n"
            f"*(Your ticket reference: `{st.session_state.ticket_id}`)*"
        )

# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🎧" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Describe your issue…"):
    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar.", icon="🔑")
        st.stop()

    # Save & show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Stream assistant reply
    client = anthropic.Anthropic(api_key=api_key)

    with st.chat_message("assistant", avatar="🎧"):
        placeholder = st.empty()
        full_response = ""

        with client.messages.stream(
            model="claude-haiku-4-5-20251001",   # fast & cost-effective for support
            max_tokens=1024,
            temperature=0.3,                     # low temp = consistent, professional tone
            system=SYSTEM_PROMPT,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
        ) as stream:
            for chunk in stream.text_stream:
                full_response += chunk
                placeholder.markdown(full_response + "▌")

        placeholder.markdown(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption(f"📧 Need more help? Email {escalation_email}")
with col2:
    st.caption(f"🎫 Ticket: `{st.session_state.ticket_id}`")
