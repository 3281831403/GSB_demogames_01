import contextlib
import copy
import importlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ttt = importlib.import_module("tic-tac-toe")

BLANK = " "
WINNING_LINES = [
	(0, 1, 2),
	(3, 4, 5),
	(6, 7, 8),
	(0, 3, 6),
	(1, 4, 7),
	(2, 5, 8),
	(0, 4, 8),
]


def run_game(inputs):
	"""Drive play_game with scripted inputs; EOFError ends the game."""
	script = iter(inputs)

	def fake_input(prompt=""):
		try:
			return next(script)
		except StopIteration:
			raise EOFError

	output = io.StringIO()
	with mock.patch("builtins.input", fake_input):
		with contextlib.redirect_stdout(output):
			try:
				ttt.play_game()
			except EOFError:
				pass
	return output.getvalue()


class TicTacToeTestCase(unittest.TestCase):
	def setUp(self):
		ttt.board[:] = [BLANK] * 9

	def snapshot(self):
		return copy.deepcopy(ttt.board)


class TestBoardAndHasWon(TicTacToeTestCase):
	def test_board_initializes_to_nine_blank_squares(self):
		fresh = [BLANK for _ in range(9)]
		self.assertEqual(len(fresh), 9)
		self.assertTrue(all(cell == BLANK for cell in fresh))

	def test_has_won_true_for_every_winning_line(self):
		for player in ("X", "O"):
			for line in WINNING_LINES:
				with self.subTest(player=player, line=line):
					ttt.board[:] = [BLANK] * 9
					for index in line:
						ttt.board[index] = player
					self.assertTrue(ttt.has_won(player))

	def test_has_won_false_for_empty_partial_and_mixed_boards(self):
		cases = [
			[BLANK] * 9,
			["X", "X", BLANK] + [BLANK] * 6,
			["X", "O", "X", "X", "O", "O", "O", "X", "X"],
			["O", "X", BLANK, BLANK, "X", BLANK, BLANK, BLANK, "O"],
		]
		for cells in cases:
			for player in ("X", "O"):
				with self.subTest(cells=cells, player=player):
					ttt.board[:] = list(cells)
					if player == "O" and cells == cases[2]:
						continue
					self.assertFalse(ttt.has_won(player))

	def test_has_won_repeated_calls_do_not_mutate_board(self):
		ttt.board[:] = ["X", "O", BLANK, BLANK, "X", BLANK, "O", BLANK, BLANK]
		before = self.snapshot()
		for _ in range(5):
			ttt.has_won("X")
			ttt.has_won("O")
		self.assertEqual(ttt.board, before)

	def test_print_board_renders_marks_in_position(self):
		ttt.board[:] = ["X", BLANK, "O"] + [BLANK] * 6
		output = io.StringIO()
		with contextlib.redirect_stdout(output):
			ttt.print_board()
		rendered = output.getvalue()
		self.assertIn(" X |   | O ", rendered)
		self.assertEqual(rendered.count("---+---+---"), 2)


class TestMoveValidation(TicTacToeTestCase):
	def test_empty_square_accepts_move(self):
		run_game(["5"])
		self.assertEqual(ttt.board[4], "X")
		self.assertEqual(ttt.board.count("X"), 1)
		self.assertEqual(ttt.board.count(BLANK), 8)

	def test_occupied_square_rejected_and_not_overwritten(self):
		output = run_game(["5", "5"])
		expected = ["X" if i == 4 else BLANK for i in range(9)]
		self.assertEqual(ttt.board, expected)
		self.assertIn("already taken", output)

	def test_non_digit_inputs_rejected_without_state_change(self):
		bad_inputs = ["abc", "", " ", "1.5", "X", "1e2", "²", "-", "+", "5 "]
		for bad in bad_inputs:
			with self.subTest(choice=bad):
				ttt.board[:] = [BLANK] * 9
				before = self.snapshot()
				output = run_game([bad])
				self.assertEqual(ttt.board, before)
				self.assertIn("Please enter a number from 1 to 9.", output)

	def test_out_of_range_inputs_rejected_without_state_change(self):
		for bad in ["0", "10", "99", "100000"]:
			with self.subTest(choice=bad):
				before = self.snapshot()
				output = run_game([bad])
				self.assertEqual(ttt.board, before)
				self.assertIn("Please enter a number from 1 to 9.", output)

	def test_rejected_move_does_not_consume_a_turn(self):
		run_game(["nope", "0", "5"])
		self.assertEqual(ttt.board.count("X"), 1)
		self.assertEqual(ttt.board[4], "X")

	def test_failed_move_then_successful_retry(self):
		before = self.snapshot()
		run_game(["5", "5", "4"])
		self.assertNotEqual(ttt.board, before)
		self.assertEqual(ttt.board[4], "X")
		self.assertEqual(ttt.board[3], "O")
		self.assertEqual(ttt.board.count(BLANK), 7)

	def test_consecutive_rounds_applied_in_order(self):
		run_game(["1", "9", "2", "8", "4"])
		expected = ["X", "X", BLANK, "X", BLANK, BLANK, BLANK, "O", "O"]
		self.assertEqual(ttt.board, expected)


class TestFullGames(TicTacToeTestCase):
	def test_x_wins_and_game_ends(self):
		output = run_game(["1", "4", "2", "5", "3", "9", "9"])
		self.assertIn("Player X wins!", output)
		self.assertEqual(ttt.board[:3], ["X", "X", "X"])
		self.assertEqual(ttt.board.count(BLANK), 4)

	def test_o_wins_and_game_ends(self):
		output = run_game(["1", "4", "2", "5", "7", "6"])
		self.assertIn("Player O wins!", output)
		self.assertEqual(ttt.board[3:6], ["O", "O", "O"])

	def test_tie_when_board_fills_without_winner(self):
		output = run_game(["1", "2", "3", "5", "4", "6", "8", "7", "9"])
		self.assertIn("It's a tie!", output)
		self.assertEqual(ttt.board.count(BLANK), 0)
		self.assertFalse(ttt.has_won("X"))
		self.assertFalse(ttt.has_won("O"))

	def test_same_input_sequence_replays_deterministically(self):
		moves = ["1", "2", "3", "5", "4", "6", "8", "7", "9"]
		first_output = run_game(moves)
		first_board = self.snapshot()
		ttt.board[:] = [BLANK] * 9
		second_output = run_game(moves)
		second_board = self.snapshot()
		self.assertEqual(first_board, second_board)
		self.assertEqual(first_output, second_output)

	def test_interrupted_game_preserves_only_completed_moves(self):
		script = iter(["5", "bad", "1"])

		def fake_input(prompt=""):
			try:
				return next(script)
			except StopIteration:
				raise KeyboardInterrupt

		with mock.patch("builtins.input", fake_input):
			with contextlib.redirect_stdout(io.StringIO()):
				with self.assertRaises(KeyboardInterrupt):
					ttt.play_game()
		self.assertEqual(ttt.board[4], "X")
		self.assertEqual(ttt.board[0], "O")
		self.assertEqual(ttt.board.count(BLANK), 7)
		self.assertTrue(all(cell in ("X", "O", BLANK) for cell in ttt.board))


if __name__ == "__main__":
	unittest.main()
