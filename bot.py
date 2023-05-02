import telebot
from telebot import types
from PyDictionary import PyDictionary
import os
import random
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv()

SECRET_KEY = str(os.getenv("SECRET_KEY"))
bot = telebot.TeleBot(SECRET_KEY)

# Create an instance of PyDictionary
dictionary = PyDictionary()

# Create an instance of PyDictionary
# Define a list of anagram words
anagram_words = ["astronomy", "triangle", "guitar", "elephant", "orange", "computer", "dolphin", "puzzle", "octopus", "book"]

# Define a function to create the custom keyboard
def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    definition_button = types.KeyboardButton('Get the definition')
    play_anagram_button = types.KeyboardButton('Play anagram')
    exit_button = types.KeyboardButton('Exit')
    keyboard.add(definition_button, play_anagram_button, exit_button)
    return keyboard

# Define a function to handle incoming messages
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Send a greeting message to the user
    response_text = "Hello! I am a dictionary bot. Please select an option below:\n"
    bot.reply_to(message, response_text, reply_markup=create_keyboard())

# Define a function to handle incoming messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Handle messages sent via custom keyboard
    if message.text == "Get the definition":
        # Ask the user what word to define
        response_text = "What word do you want to define?"
        bot.reply_to(message, response_text)
        bot.register_next_step_handler(message, define_word)
    elif message.text == "Play anagram":
        # Choose a random word from the anagram_words list
        anagram_word = random.choice(anagram_words)

        # Shuffle the letters of the word to create an anagram
        anagram = ''.join(random.sample(anagram_word, len(anagram_word)))

        # Send the anagram to the user
        response_text = f"Unscramble the word: {anagram}"
        bot.reply_to(message, response_text)

        # Register the next step to handle the user's answer
        bot.register_next_step_handler(message, handle_anagram, anagram_word)
    elif message.text == "Exit":
        handle_exit(message)

# Define a function to handle the user's response to the anagram
def handle_anagram(message, anagram_word):
    # Get the user's answer from the message text
    answer = message.text

    # Check if the answer is correct
    if answer.lower() == anagram_word:
        response_text = "Correct! Well done."
    else:
        response_text = "Sorry, that's incorrect. Try again."

    # Send the response to the user
    bot.reply_to(message, response_text)

    # Register the next step to ask the user what to do next
    response_text = "What would you like to do next?"
    bot.reply_to(message, response_text, reply_markup=create_keyboard())


# Define a function to handle the user's response to the word to define
def define_word(message):
    # Get the word to define from the message text
    word = message.text

    # Use PyDictionary to get the definition
    definition = dictionary.meaning(word)

    # Format the definition as a string
    response_text = f"Definition of '{word}':\n"
    for key in definition:
        response_text += f"{key.capitalize()}:\n"
        for item in definition[key]:
            response_text += f"- {item}\n"

    # Send the definition as a message to the user
    bot.reply_to(message, response_text)

# Start the bot and wait for incoming messages
bot.polling()

#bot.polling(non_stop=True)
