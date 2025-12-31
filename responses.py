import random
import datetime

class ChatResponses:
    @staticmethod
    def get_response(user_input):
        """Get appropriate response based on user input"""
        input_lower = user_input.lower()
        
        # Greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon']
        if any(greet in input_lower for greet in greetings):
            return random.choice([
                "Hello! Nice to meet you!",
                "Hi there! How can I help?",
                "Hey! What's up?",
                "Greetings! How are you today?"
            ])
        
        # How are you
        if 'how are you' in input_lower:
            return random.choice([
                "I'm doing great, thanks for asking!",
                "I'm excellent! Always ready to help.",
                "Doing well! How about you?",
                "I'm functioning optimally, thank you!"
            ])
        
        # Name
        if 'your name' in input_lower or 'who are you' in input_lower:
            return "I'm VoiceBot, your personal voice assistant. I'm here to help you!"
        
        # Time
        if 'time' in input_lower and ('current' in input_lower or 'what' in input_lower):
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"
        
        # Date
        if 'date' in input_lower and ('today' in input_lower or 'what' in input_lower):
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            return f"Today is {current_date}"
        
        # Weather (placeholder)
        if 'weather' in input_lower:
            return "I'm currently offline for weather updates, but you can check your local weather service!"
        
        # Math (simple calculations)
        if 'plus' in input_lower or '+' in input_lower:
            try:
                # Extract numbers (simple version)
                words = input_lower.split()
                nums = [int(word) for word in words if word.isdigit()]
                if len(nums) >= 2:
                    return f"{nums[0]} plus {nums[1]} equals {nums[0] + nums[1]}"
            except:
                pass
        
        # Jokes
        if 'joke' in input_lower:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "What do you call a bear with no teeth? A gummy bear!"
            ]
            return random.choice(jokes)
        
        # Help
        if 'help' in input_lower:
            return """I can help you with:
            - Telling time and date
            - Simple calculations
            - Telling jokes
            - Answering basic questions
            Just ask me anything!"""
        
        # Default responses
        default_responses = [
            "That's interesting! Tell me more.",
            "I see. What else would you like to know?",
            "I'm still learning, but I'll remember that.",
            "Could you rephrase that?",
            "Let me think about that... In the meantime, ask me something else!",
            f"You said: '{user_input}'. I'm processing that information."
        ]
        
        return random.choice(default_responses)