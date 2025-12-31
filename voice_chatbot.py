import speech_recognition as sr
import pyttsx3
import time
from responses import ChatResponses  # Import our response handler

class VoiceChatbot:
    def __init__(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Configure voice properties
        self.configure_voice()
        
        print("🤖 Voice Chatbot v1.0 Initialized!")
        print("=" * 50)
    
    def configure_voice(self):
        """Configure TTS voice settings"""
        voices = self.engine.getProperty('voices')
        
        # Try to use a female voice if available
        try:
            self.engine.setProperty('voice', voices[1].id)  # Usually index 1 is female
        except:
            pass  # Use default voice
        
        self.engine.setProperty('rate', 160)  # Speech speed
        self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    def speak(self, text):
        """Convert text to speech with visual feedback"""
        print(f"\n{'='*50}")
        print(f"🤖 BOT: {text}")
        print(f"{'='*50}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen(self):
        """Listen to microphone and convert to text"""
        with sr.Microphone() as source:
            print("\n" + "🎙️" * 10)
            print("🎤 LISTENING... (Speak clearly)")
            
            try:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=3, 
                    phrase_time_limit=7
                )
                
                # Convert to text
                text = self.recognizer.recognize_google(audio)
                print(f"\n👤 YOU: {text}")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("⏰ No speech detected within 3 seconds")
                return ""
            except sr.UnknownValueError:
                print("❌ Speech was unclear")
                return ""
            except sr.RequestError as e:
                print(f"🌐 API Error: {e}")
                return ""
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}")
                return ""
    
    def run(self):
        """Main chatbot loop"""
        # Welcome
        welcome_msg = """Welcome to VoiceBot! 
        I can help you with various tasks. 
        Say 'help' to see what I can do, or 'exit' to quit."""
        self.speak(welcome_msg)
        
        conversation_count = 0
        
        while True:
            conversation_count += 1
            
            # Get user input
            user_input = self.listen()
            
            # Skip if empty input
            if not user_input:
                continue
            
            # Check for exit
            exit_words = ['exit', 'quit', 'stop', 'goodbye', 'bye']
            if any(word in user_input for word in exit_words):
                farewells = [
                    "Goodbye! It was nice talking to you!",
                    "See you later! Have a great day!",
                    "Bye! Come back anytime!"
                ]
                import random
                self.speak(random.choice(farewells))
                print(f"\n📊 Session Summary:")
                print(f"   Conversations: {conversation_count}")
                print(f"   Chatbot session ended successfully!")
                break
            
            # Get response
            response = ChatResponses.get_response(user_input)
            
            # Speak response
            self.speak(response)

def main():
    """Main function"""
    print("Starting Voice Chatbot...")
    print("Make sure your microphone is connected and working.")
    print("Press Ctrl+C to exit at any time.\n")
    
    try:
        # Create and run chatbot
        chatbot = VoiceChatbot()
        chatbot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Program interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Please check your microphone and try again.")

if __name__ == "__main__":
    main()