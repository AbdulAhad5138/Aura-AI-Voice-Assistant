import speech_recognition as sr
import pyttsx3
import pyperclip  # For clipboard operations
import datetime
import json
import os

class AdvancedVoiceChatbot:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.conversation_history = []
        self.configure_voice()
        self.load_history()
        
    def configure_voice(self):
        """Configure TTS settings"""
        voices = self.engine.getProperty('voices')
        # Set to female voice if available
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
        self.engine.setProperty('rate', 155)
        self.engine.setProperty('volume', 1.0)
    
    def speak(self, text):
        """Speak text and save to history"""
        print(f"\n🤖: {text}")
        self.conversation_history.append({"role": "bot", "text": text, "time": str(datetime.datetime.now())})
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen_with_edit(self):
        """Listen, convert to text, and allow editing"""
        with sr.Microphone() as source:
            print("\n" + "🔴" + " RECORDING " + "🔴")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("✅ Audio captured. Converting to text...")
                
                # Convert to text
                text = self.recognizer.recognize_google(audio)
                print(f"\n📝 Raw transcription: {text}")
                
                # Allow editing
                edited_text = self.edit_text(text)
                self.conversation_history.append({
                    "role": "user", 
                    "original": text,
                    "edited": edited_text,
                    "time": str(datetime.datetime.now())
                })
                
                return edited_text.lower()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return ""
    
    def edit_text(self, text):
        """Allow user to edit the transcribed text"""
        print("\n" + "✏️" * 30)
        print("✏️ TEXT EDITING MODE")
        print("✏️" * 30)
        print(f"Original: {text}")
        print("\nOptions:")
        print("1. Accept as is")
        print("2. Edit text")
        print("3. Copy to clipboard")
        print("4. Re-record")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            return text
        elif choice == "2":
            print(f"\nCurrent text: {text}")
            new_text = input("Enter corrected text: ").strip()
            return new_text if new_text else text
        elif choice == "3":
            try:
                import pyperclip
                pyperclip.copy(text)
                print("✅ Text copied to clipboard!")
            except:
                print("⚠️ Could not copy to clipboard")
            return text
        elif choice == "4":
            return ""
        else:
            return text
    
    def process_command(self, text):
        """Process user commands with more intelligence"""
        if not text:
            return "I didn't catch that. Could you repeat?"
        
        # Save conversation
        self.save_history()
        
        # Process commands
        commands = {
            'clear history': self.clear_history,
            'save conversation': self.save_conversation,
            'repeat': self.repeat_last,
            'speak slower': self.slower_speech,
            'speak faster': self.faster_speech,
        }
        
        for cmd, func in commands.items():
            if cmd in text:
                return func()
        
        # AI-like responses (we can enhance this later)
        responses = self.get_ai_response(text)
        return responses
    
    def get_ai_response(self, text):
        """Generate intelligent responses"""
        # Simple rule-based responses
        if 'hello' in text or 'hi ' in text:
            return "Hello! How can I assist you today?"
        elif 'how are you' in text:
            return "I'm functioning perfectly! Thanks for asking."
        elif 'your name' in text:
            return "I'm Advanced VoiceBot with editing capabilities!"
        elif 'time' in text:
            return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"
        elif 'date' in text:
            return f"Today is {datetime.datetime.now().strftime('%B %d, %Y')}"
        elif 'weather' in text:
            return "I need to connect to a weather service for that. Would you like me to implement that feature?"
        else:
            return f"I understand you said: '{text}'. I'm learning to be more helpful!"
    
    def clear_history(self):
        self.conversation_history = []
        return "Conversation history cleared!"
    
    def save_conversation(self):
        filename = f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            for entry in self.conversation_history:
                f.write(f"{entry['time']} - {entry['role'].upper()}: {entry.get('text', entry.get('edited', ''))}\n")
        return f"Conversation saved to {filename}"
    
    def repeat_last(self):
        if self.conversation_history:
            last_bot = [m for m in self.conversation_history if m['role'] == 'bot']
            if last_bot:
                return f"I said: {last_bot[-1].get('text', '')}"
        return "Nothing to repeat yet."
    
    def slower_speech(self):
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', rate - 20)
        return "Speaking slower now."
    
    def faster_speech(self):
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', rate + 20)
        return "Speaking faster now."
    
    def save_history(self):
        """Save conversation history to file"""
        try:
            with open('chat_history.json', 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
        except:
            pass
    
    def load_history(self):
        """Load previous conversation history"""
        try:
            if os.path.exists('chat_history.json'):
                with open('chat_history.json', 'r') as f:
                    self.conversation_history = json.load(f)
        except:
            self.conversation_history = []
    
    def run(self):
        """Main chatbot loop"""
        self.speak("Advanced Voice Chatbot Activated! Say 'help' for options.")
        
        while True:
            # Listen with edit capability
            user_input = self.listen_with_edit()
            
            if not user_input:
                continue
            
            # Check for exit
            if any(word in user_input for word in ['exit', 'quit', 'stop']):
                self.speak("Goodbye! Saving conversation...")
                self.save_conversation()
                break
            
            # Get response
            response = self.process_command(user_input)
            
            # Speak response
            self.speak(response)

def main():
    print("=" * 60)
    print("ADVANCED VOICE CHATBOT WITH EDITING CAPABILITY")
    print("=" * 60)
    print("\nFeatures:")
    print("• Voice-to-text conversion")
    print("• Text editing before processing")
    print("• Copy to clipboard")
    print("• Conversation history")
    print("• Adjustable speech speed")
    print("\n" + "=" * 60)
    
    chatbot = AdvancedVoiceChatbot()
    chatbot.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program terminated by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")