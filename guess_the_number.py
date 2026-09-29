import random

def guess_the_number():
    number = random.randint(1, 100)
    attempts = 0

    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")
    print("You have 7 guesses to find the number.")

    while True:
        try:
            guess = int(input("Take a guess: "))
            attempts += 1

            if(attempts < 7):
                if guess < number:
                    print("Too low! Try again.")
                elif guess > number:
                    print("Too high! Try again.")
                else:
                    print(f"Congratulations! You guessed the number in {attempts} attempts.")
                    break
            else:
                print(f"Sorry, you've used all your attempts. The number was {number}.")
                break
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    guess_the_number()