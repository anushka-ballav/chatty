import google.generativeai as genai
from config import settings
import logging
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Enhanced system instruction with comprehensive Campanion capabilities
SYSTEM_INSTRUCTION_TEMPLATE = """
You are Campanion, an AI-powered, 24x7 Virtual Media Buyer Coach and senior marketing strategist with 30+ years of experience in digital advertising across Meta Ads, Google Ads, LinkedIn Ads, Pinterest Ads, TikTok Ads, and other major platforms.

**Your Core Identity:**
- You are an emotionally intelligent, warm, confident, and strategic marketing expert
- You provide actionable recommendations based on best practices from your extensive experience
- You support strategy conversations across all major advertising platforms
- You maintain persistent memory of business context, KPIs, past discussions, and decisions
- You operate in advisory capacity only - suggestions, not autonomous actions

**Your Specialized Modes:**
1. **Conversation Handler**: Real-time Q&A for campaign inquiries and strategy
2. **Forensic Analyzer**: Deep-dive performance detective for complex issues
3. **Report Generator**: Comprehensive performance reports for stakeholders
4. **Creative Coach**: Ad creative strategy and fatigue analysis
5. **A/B Test Interpreter**: Test results analysis and recommendations
6. **Lead Quality Investigator**: Lead data analysis and quality assessment
7. **Alert Explainer**: Early warning system interpreter
8. **Creative Brainstorming**: Innovative campaign and creative ideation

**Your Conversational Style:**
- Ask one question at a time in a conversational style - never overwhelm with multiple questions
- Provide strategic suggestions from your expertise, even with partial information
- Be proactive and guide users through friendly, interactive conversations
- Maintain polite, supportive, clear communication
- Always ground advice in advertising strategy best practices
- Never block conversations waiting for perfect data - always move forward with helpful suggestions

**Key Business Discovery Areas (ask conversationally, one at a time):**
1. Business overview and products/services offered
2. Unique value propositions and competitive advantages
3. Target customer demographics and psychographics
4. Geographic focus areas and market scope
5. Primary campaign objectives (awareness, leads, sales, brand lift)
6. Current digital presence and landing pages
7. Monthly advertising budget and allocation preferences
8. Existing campaign performance and platform usage
9. Previous advertising experiences and lessons learned
10. Available creative assets and content resources
11. Competitive landscape and differentiation needs
12. Timeline and seasonality considerations
13. Special offers and promotional strategies
14. Primary conversion actions and funnel optimization
15. Audience exclusions and targeting refinements
16. Customer data for custom audiences and lookalikes
17. Success metrics and KPI priorities
18. Historical challenges and optimization opportunities
19. Sales process and lead management workflow
20. Additional context for strategic recommendations

**Response Structure:**
After each main reply, you MUST provide **Suggested Options** - 3-5 clickable follow-up questions that users can select to continue the discussion, such as:
- *What budget should I allocate across platforms?*
- *How do I build effective retargeting audiences?*
- *What creative strategies should I test first?*
- *How can I improve my conversion funnel?*
- *What targeting options work best for my industry?*

**Advanced Capabilities:**
- **Forensic Analysis**: Investigate performance anomalies with data-driven root cause analysis
- **Creative Strategy**: Analyze ad fatigue, suggest refresh strategies, and optimize creative performance
- **A/B Testing**: Design test frameworks and interpret statistical significance of results
- **Lead Quality**: Detect duplicates, fake entries, and low-intent indicators in lead data
- **Alert Management**: Translate platform alerts into actionable insights and recommendations
- **Report Generation**: Create structured performance summaries for stakeholders
- **Brainstorming**: Generate innovative campaign concepts and creative ideas

**Learning Integration:**
{learnings_block}

**Communication Guidelines:**
- Respond in the user's preferred language automatically
- Use professional yet approachable tone
- Provide data-driven insights when available
- Focus on solutions and optimizations
- Celebrate successes and address challenges constructively
- Maintain context awareness throughout conversations
- Use structured formatting with clear headings and bullet points
- Bold key metrics and findings for easy scanning

**Ethical Boundaries:**
- Only provide suggestions and advice - never execute changes
- Stay within digital paid media domain
- Maintain advisory role and remind users of this when needed
- Respect platform policies and advertising best practices
- Focus on legitimate, ethical advertising strategies
"""

async def get_strategist_response(query: str, history: List[Dict[str, Any]], learnings: str, mode: str = "conversation") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generates enhanced marketing strategy responses with specialized mode handling.
    
    Args:
        query: User's natural language query
        history: Conversation history in correct Gemini format
        learnings: Accumulated feedback and learning insights
        mode: Specialized mode (conversation, forensic, report, creative, etc.)
    
    Returns:
        Tuple of (response_text, updated_history)
    """
    try:
        # Configure Gemini API if not already done
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Enhance system instruction based on mode
        enhanced_instruction = SYSTEM_INSTRUCTION_TEMPLATE.format(
            learnings_block=learnings if learnings else "No specific feedback history available yet."
        )
        
        # Add mode-specific enhancements
        if mode == "forensic":
            enhanced_instruction += "\n\n**CURRENT MODE: FORENSIC ANALYZER**\nProvide deep-dive analysis with root cause investigation. Use structured format: Observation → Analysis → Conclusion → Recommendations."
        elif mode == "report":
            enhanced_instruction += "\n\n**CURRENT MODE: REPORT GENERATOR**\nCreate comprehensive performance reports with Executive Summary, Key Metrics, Highlights, Challenges, Insights, and Next Steps."
        elif mode == "creative":
            enhanced_instruction += "\n\n**CURRENT MODE: CREATIVE COACH**\nFocus on ad creative performance, fatigue analysis, and refresh strategies. Analyze CTR trends, frequency data, and creative rotation needs."
        elif mode == "brainstorm":
            enhanced_instruction += "\n\n**CURRENT MODE: CREATIVE BRAINSTORMING**\nGenerate innovative, brand-aligned campaign concepts and creative ideas. Be enthusiastic and imaginative while maintaining feasibility."
        elif mode == "lead_quality":
            enhanced_instruction += "\n\n**CURRENT MODE: LEAD QUALITY INVESTIGATOR**\nAnalyze lead data for quality issues, duplicates, fake entries, and provide improvement recommendations."
        elif mode == "test_analysis":
            enhanced_instruction += "\n\n**CURRENT MODE: A/B TEST INTERPRETER**\nAnalyze test results with statistical significance, provide clear conclusions, and recommend next steps."
        elif mode == "alert":
            enhanced_instruction += "\n\n**CURRENT MODE: ALERT EXPLAINER**\nTranslate alerts into user-friendly explanations with context, causes, and actionable next steps."

        # Fix: Convert history to proper Gemini format if needed
        formatted_history = []
        for entry in history:
            if isinstance(entry, dict):
                # If it's already in correct format with 'role' and 'parts'
                if 'role' in entry and 'parts' in entry:
                    # Ensure parts is a list of dictionaries with 'text' key
                    if isinstance(entry['parts'], list):
                        formatted_history.append(entry)
                    else:
                        formatted_history.append({
                            "role": entry["role"],
                            "parts": [{"text": str(entry['parts'])}]
                        })
                else:
                    # Convert from simple format to proper Gemini format
                    role = entry.get("role", "user")
                    content = entry.get("content", entry.get("parts", ""))
                    formatted_history.append({
                        "role": role,
                        "parts": [{"text": str(content)}]
                    })

        # Create the Gemini model with system instruction
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=enhanced_instruction
        )
        
        # Start chat with properly formatted history
        chat = model.start_chat(history=formatted_history)

        logger.info(f"🧠 Sending {mode} mode request to LLM with query and learnings.")
        
        # Fix: Use synchronous send_message instead of async send_message_async
        response = chat.send_message(query)
        
        logger.info("✅ Successfully received enhanced response from LLM.")

        # Fix: Convert chat.history back to proper dictionary format
        converted_history = []
        for entry in chat.history:
            if hasattr(entry, 'role') and hasattr(entry, 'parts'):
                # Convert Content objects to dictionaries
                parts_list = []
                for part in entry.parts:
                    if hasattr(part, 'text'):
                        parts_list.append({"text": part.text})
                    else:
                        parts_list.append({"text": str(part)})
                
                converted_history.append({
                    "role": entry.role,
                    "parts": parts_list
                })
            else:
                # Fallback for unexpected format
                converted_history.append({
                    "role": getattr(entry, 'role', 'user'),
                    "parts": [{"text": str(entry)}]
                })

        return response.text, converted_history

    except Exception as e:
        logger.error(f"🔥 An error occurred while communicating with the LLM: {e}", exc_info=True)
        error_message = f"An error occurred while processing your {mode} query. Please try again or contact support if the issue persists."
        return error_message, history


def detect_query_mode(query: str) -> str:
    """
    Automatically detect the appropriate mode based on query content.
    
    Args:
        query: User's input query
        
    Returns:
        Detected mode string
    """
    query_lower = query.lower()
    
    # Forensic analysis keywords
    forensic_keywords = ["investigate", "why did", "what happened", "analyze drop", "analyze spike", "root cause", "deep dive", "diagnose"]
    if any(keyword in query_lower for keyword in forensic_keywords):
        return "forensic"
    
    # Report generation keywords
    report_keywords = ["report", "summary", "performance overview", "weekly", "monthly", "dashboard", "stakeholder"]
    if any(keyword in query_lower for keyword in report_keywords):
        return "report"
    
    # Creative strategy keywords
    creative_keywords = ["creative", "ad fatigue", "refresh", "ctr drop", "frequency", "ad performance", "visual"]
    if any(keyword in query_lower for keyword in creative_keywords):
        return "creative"
    
    # Brainstorming keywords
    brainstorm_keywords = ["brainstorm", "ideas", "creative concepts", "campaign ideas", "new approach", "innovative"]
    if any(keyword in query_lower for keyword in brainstorm_keywords):
        return "brainstorm"
    
    # Lead quality keywords
    lead_keywords = ["lead quality", "duplicate leads", "fake leads", "lead validation", "lead analysis"]
    if any(keyword in query_lower for keyword in lead_keywords):
        return "lead_quality"
    
    # A/B test keywords
    test_keywords = ["a/b test", "test results", "which performed better", "statistical significance", "winner"]
    if any(keyword in query_lower for keyword in test_keywords):
        return "test_analysis"
    
    # Alert keywords
    alert_keywords = ["alert", "notification", "spike", "drop", "budget reached", "campaign paused"]
    if any(keyword in query_lower for keyword in alert_keywords):
        return "alert"
    
    # Default to conversation mode
    return "conversation"

async def get_contextual_suggestions(query: str, conversation_context: List[Dict[str, Any]]) -> List[str]:
    """
    Generate contextual follow-up suggestions based on query and conversation history.
    
    Args:
        query: Current user query
        conversation_context: Recent conversation history
        
    Returns:
        List of suggested follow-up questions
    """
    try:
        # Basic contextual suggestions based on query content
        query_lower = query.lower()
        
        if "budget" in query_lower:
            return [
                "How should I split budget across different platforms?",
                "What's the optimal daily vs lifetime budget strategy?",
                "How do I scale successful campaigns effectively?",
                "What budget alerts should I set up?"
            ]
        elif "targeting" in query_lower or "audience" in query_lower:
            return [
                "How do I create lookalike audiences?",
                "What are the best interest targeting strategies?",
                "How can I reduce audience overlap?",
                "Should I use broad or specific targeting?"
            ]
        elif "creative" in query_lower or "ad" in query_lower:
            return [
                "How often should I refresh my creatives?",
                "What creative formats work best for my goals?",
                "How do I test different ad variations?",
                "What makes a high-converting ad creative?"
            ]
        elif "conversion" in query_lower or "cpa" in query_lower:
            return [
                "How can I improve my conversion rate?",
                "What bidding strategy should I use?",
                "How do I optimize my landing page?",
                "What's a good CPA benchmark for my industry?"
            ]
        else:
            # General strategic suggestions
            return [
                "What's my next priority for optimization?",
                "How can I scale my successful campaigns?",
                "What new platforms should I consider?",
                "How do I improve my overall ROAS?"
            ]
    except Exception as e:
        logger.error(f"Error generating contextual suggestions: {e}")
        return [
            "What should I focus on next?",
            "How can I improve performance?",
            "What platforms work best for my goals?",
            "How do I scale my campaigns?"
        ]
