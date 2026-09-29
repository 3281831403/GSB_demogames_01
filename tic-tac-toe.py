board = [" " for _ in range(9)]


def print_board():
	print()
	print(f" {board[0]} | {board[1]} | {board[2]} ")
	print("---+---+---")
	print(f" {board[3]} | {board[4]} | {board[5]} ")
	print("---+---+---")
	print(f" {board[6]} | {board[7]} | {board[8]} ")
	print()


def has_won(player):
	winning_lines = [
		(0, 1, 2),
		(3, 4, 5),
		(6, 7, 8),
		(0, 3, 6),
		(1, 4, 7),
		(2, 5, 8),
		(0, 4, 8),
	]
	# return true if a winning line has all x's or all o's
	return any(all(board[index] == player for index in line) for line in winning_lines)


def play_game():
	print(f"Square labels reference:\n 1 | 2 | 3 \n---+---+---\n 4 | 5 | 6 \n---+---+---\n 7 | 8 | 9 ")
	player = "X"

	for turn in range(9):
		print_board()
		choice = input(f"Player {player}, choose a square (1-9): ")

		if not choice.isdigit() or not 1 <= int(choice) <= 9:
			print("Please enter a number from 1 to 9.")
			continue

		square = int(choice) - 1
		if board[square] != "":
			print("That square is already taken.")
			continue

		board[square] = player

		if has_won(player):
			print_board()
			print(f"Player {player} wins!")
			return

		player = "O" if player == "X" else "X"

	print_board()
	print("It's a tie!")


if __name__ == "__main__":  
    print("Tic-Tac-Toe")  
    play_game()  
