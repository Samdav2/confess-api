from groq import AsyncGroq
from fastapi import HTTPException, status
import logging
import asyncio

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_key: str):
        if not api_key:
            logger.warning("Groq API key is missing")
            self.client = None
            return

        self.client = AsyncGroq(api_key=api_key)
        # Using Llama 3.3 70B for high quality generation
        self.model_name = 'llama-3.3-70b-versatile'

    async def generate_confession_message(
        self,
        tone: str,
        confess_type: str,
        recipient_name: str
    ) -> str:
        """
        Generate a confession message using Groq AI.
        """
        prompt = f"""
        You are a master communicator with deep expertise in psychology, emotional intelligence, and the human condition. Your specialty is translating raw, complex human emotions into words that resonate at a soul level.

        CONTEXT:
        Someone is about to share something deeply personal—a {confess_type}. This moment matters to them. They've chosen {recipient_name or 'someone important'} as the recipient because this person holds significance in their life.

        YOUR MISSION:
        Craft a message that doesn't just convey information, but transmits feeling. The reader should sense the vulnerability, authenticity, and humanity behind every word.

        PARAMETERS:
        - Confession Type: {confess_type}
        - Emotional Tone: {tone}
        - Recipient: {recipient_name or 'Friend'}
        - Length: Minimum 80 words

        PSYCHOLOGICAL APPROACH:
        1. **Emotional Authenticity**: Tap into the raw, unfiltered emotion beneath the confession type. If it's love, access the yearning and hope. If it's apology, feel the weight of regret and the desire for healing. If it's gratitude, channel the warmth of recognition.

        2. **Tonal Embodiment**: The {tone} isn't just stylistic—it's the emotional container. A humorous tone might use levity to soften vulnerability. A romantic tone invites intimacy. An apologetic tone requires humility. Let the tone shape every word choice.

        3. **Relational Awareness**: This message exists in a relationship. Consider the unspoken history, the shared moments, the emotional vocabulary unique to these two people. Make it feel personal, not generic.

        4. **Sensory and Concrete Language**: Avoid abstractions. Use imagery, metaphor, and specific details that make the emotion tangible. Instead of "I care about you," try "Your laugh has become the sound I listen for in crowded rooms."

        5. **Rhythm and Breath**: Write as if speaking from the heart. Vary sentence length. Let emotion create natural pauses. Build to moments of emphasis.

        6. **Vulnerability as Strength**: The courage to confess is powerful. Let that bravery show through honest, unguarded language.

        OUTPUT REQUIREMENTS:
        - Write ONLY the confession message itself
        - No quotation marks, no preambles, no meta-commentary
        - Make it sound like a real person speaking their truth
        - Let imperfection show—real emotion isn't polished
        - Aim for 80-150 words unless the emotion naturally requires more

        Remember: This message might be read and re-read. It might be saved, cherished, or become a turning point in someone's life. Honor that weight.

        Begin:
        """

        max_retries = 3
        retry_delay = 1  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                if not self.client:
                     logger.error("Groq Client is None. API Key likely missing.")
                     raise ValueError("Groq API Key is missing.")

                response = await self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model_name,
                    temperature=0.3,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content

                if content:
                    return content.strip()
                else:
                    logger.warning("Empty response from Groq API")
                    raise ValueError("Empty response from API")

            except Exception as e:
                logger.exception(f"Attempt {attempt + 1}/{max_retries} failed to generate Groq content")
                error_msg = str(e)

                # If safety filter is triggered (Groq content filtering), handle it?
                # Groq raises BadRequestError for safety usually.
                if "safety" in error_msg.lower():
                     logger.warning(f"Groq safety filter triggered: {error_msg}")
                     raise HTTPException(
                         status_code=status.HTTP_400_BAD_REQUEST,
                         detail="The request was flagged by safety filters. Please rephrase."
                     )

                # If this was the last attempt, don't sleep
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} attempts to generate content failed.")
                    return (
                        f"Sometimes words fail to capture what's in the heart, but my feelings are real. "
                        f"I wanted to share this confession with you, {recipient_name or 'Friend'}, "
                        f"to let you know how much you mean to me and that I'm thinking of you sincerely."
                    )
