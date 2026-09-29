import contextlib
import copy
import importlib.util
import io
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parent / "tic-tac-toe.py"


def load_module():
	spec = importlib.util.spec_from_file_location("tic_tac_toe", MODULE_PATH)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def run_game(module, inputs):
	module.board = [" " for _ in range(9)]
	buffer = io.StringIO()
	with mock.patch("builtins.input", side_effect=list(inputs)), contextlib.redirect_stdout(buffer):
		module.play_game()
	return list(module.board), buffer.getvalue()


class EmptySquareTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_empty_square_accepts_move(self):
		board, _ = run_game(self.ttt, ["1", "4", "2", "5", "3"])
		self.assertEqual(board[0], "X")

	def test_all_empty_squares_accept_moves_in_any_order(self):
		full_games = {
			"1": ["1", "2", "3", "5", "4", "6", "8", "7", "9"],
			"3": ["3", "2", "1", "5", "4", "6", "8", "7", "9"],
			"5": ["5", "2", "1", "4", "3", "8", "6", "9", "7"],
			"7": ["7", "2", "1", "4", "3", "8", "5", "9", "6"],
			"9": ["9", "2", "1", "5", "3", "6", "4", "7", "8"],
		}
		for first, inputs in full_games.items():
			with self.subTest(first=first):
				board, _ = run_game(self.ttt, inputs)
				self.assertEqual(board[int(first) - 1], "X")

	def test_out_of_order_inputs_fill_correct_squares(self):
		board, _ = run_game(self.ttt, ["9", "1", "5", "2", "8", "6", "3", "4", "7"])
		self.assertEqual(board[8], "X")
		self.assertEqual(board[0], "O")
		self.assertEqual(board[4], "X")


class OccupiedSquareTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_occupied_square_rejected_and_not_overwritten(self):
		inputs = ["1", "1", "4", "2", "5", "3"]
		self.ttt.board = [" " for _ in range(9)]
		snapshots = []

		def fake_input(prompt=""):
			choice = inputs.pop(0)
			snapshots.append((choice, copy.deepcopy(self.ttt.board)))
			return choice

		with mock.patch("builtins.input", side_effect=fake_input), contextlib.redirect_stdout(io.StringIO()):
			self.ttt.play_game()

		rejected_choice, before = snapshots[1]
		self.assertEqual(rejected_choice, "1")
		self.assertEqual(before[0], "X")

	def test_occupied_square_rolls_back_field_by_field(self):
		inputs = ["5", "5", "1", "2", "3", "4", "6", "7", "8"]
		self.ttt.board = [" " for _ in range(9)]
		before_each = []
		after_each = []

		def fake_input(prompt=""):
			before_each.append(copy.deepcopy(self.ttt.board))
			return inputs.pop(0)

		real_print_board = self.ttt.print_board

		def tracking_print_board():
			after_each.append(copy.deepcopy(self.ttt.board))
			real_print_board()

		with mock.patch("builtins.input", side_effect=fake_input), \
				mock.patch.object(self.ttt, "print_board", side_effect=tracking_print_board), \
				contextlib.redirect_stdout(io.StringIO()):
			self.ttt.play_game()

		# turn 2 is the rejected duplicate of square 5: state must be untouched
		self.assertEqual(before_each[1], before_each[2])
		self.assertEqual(before_each[1][4], "X")

	def test_occupied_message_printed(self):
		_, output = run_game(self.ttt, ["1", "1", "4", "2", "5", "3"])
		self.assertIn("already taken", output)


class InvalidInputTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_out_of_range_rejected_without_crash(self):
		for bad in ("0", "10", "99", "1000"):
			with self.subTest(bad=bad):
				board, output = run_game(self.ttt, [bad, "1", "4", "2", "5", "3"])
				self.assertIn("Please enter a number from 1 to 9.", output)
				self.assertEqual(len(board), 9)

	def test_non_numeric_rejected_without_crash(self):
		for bad in ("abc", "", "1.5", "x", "-1", " 1", "1 "):
			with self.subTest(bad=bad):
				board, output = run_game(self.ttt, [bad, "1", "4", "2", "5", "3"])
				self.assertIn("Please enter a number from 1 to 9.", output)
				self.assertEqual(len(board), 9)

	def test_invalid_input_does_not_mutate_board(self):
		self.ttt.board = [" " for _ in range(9)]
		snapshot = copy.deepcopy(self.ttt.board)
		inputs = ["zz", "0", "42", "1", "4", "2", "5", "3"]
		seen = []

		def tracking_input(prompt=""):
			seen.append(copy.deepcopy(self.ttt.board))
			return inputs.pop(0)

		with mock.patch("builtins.input", side_effect=tracking_input), contextlib.redirect_stdout(io.StringIO()):
			self.ttt.play_game()

		for state in seen[:3]:
			self.assertEqual(state, snapshot)

	def test_failure_then_success_unaffected(self):
		board, output = run_game(self.ttt, ["nope", "0", "1", "4", "2", "5", "3"])
		self.assertEqual(board[0], "X")
		self.assertIn("Player X wins!", output)


class WinAndTieTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_x_wins(self):
		board, output = run_game(self.ttt, ["1", "4", "2", "5", "3"])
		self.assertIn("Player X wins!", output)
		self.assertEqual(board[:3], ["X", "X", "X"])

	def test_o_wins(self):
		board, output = run_game(self.ttt, ["1", "4", "2", "5", "9", "6"])
		self.assertIn("Player O wins!", output)
		self.assertEqual([board[3], board[4], board[5]], ["O", "O", "O"])

	def test_tie_after_nine_moves(self):
		board, output = run_game(self.ttt, ["1", "2", "3", "5", "4", "6", "8", "7", "9"])
		self.assertIn("It's a tie!", output)
		self.assertNotIn(" ", board)

	def test_consecutive_turns_fill_board(self):
		board, _ = run_game(self.ttt, ["1", "2", "3", "5", "4", "6", "8", "7", "9"])
		self.assertEqual(board.count("X"), 5)
		self.assertEqual(board.count("O"), 4)


class HasWonTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_has_won_true_for_each_winning_line(self):
		lines = [
			(0, 1, 2), (3, 4, 5), (6, 7, 8),
			(0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8),
		]
		for line in lines:
			for player in ("X", "O"):
				with self.subTest(line=line, player=player):
					self.ttt.board = [" " for _ in range(9)]
					for index in line:
						self.ttt.board[index] = player
					self.assertTrue(self.ttt.has_won(player))

	def test_has_won_false_on_empty_board(self):
		self.ttt.board = [" " for _ in range(9)]
		self.assertFalse(self.ttt.has_won("X"))
		self.assertFalse(self.ttt.has_won("O"))

	def test_has_won_false_on_partial_line(self):
		self.ttt.board = [" " for _ in range(9)]
		self.ttt.board[0] = "X"
		self.ttt.board[1] = "X"
		self.assertFalse(self.ttt.has_won("X"))

	def test_has_won_repeated_calls_consistent(self):
		self.ttt.board = ["X", "X", "X"] + [" " for _ in range(6)]
		results = {self.ttt.has_won("X") for _ in range(5)}
		self.assertEqual(results, {True})


class DeterminismAndStateTests(unittest.TestCase):
	def setUp(self):
		self.ttt = load_module()

	def test_same_input_sequence_replays_identically(self):
		inputs = ["bad", "1", "1", "4", "2", "5", "3"]
		board_a, output_a = run_game(self.ttt, inputs)
		board_b, output_b = run_game(self.ttt, inputs)
		self.assertEqual(board_a, board_b)
		self.assertEqual(output_a, output_b)

	def test_repeated_games_after_reset(self):
		for _ in range(3):
			board, output = run_game(self.ttt, ["1", "4", "2", "5", "3"])
			self.assertIn("Player X wins!", output)
			self.assertEqual(board[:3], ["X", "X", "X"])

	def test_board_stays_bounded_after_full_game(self):
		board, _ = run_game(self.ttt, ["1", "2", "3", "5", "4", "6", "8", "7", "9"])
		self.assertEqual(len(board), 9)
		self.assertTrue(all(cell in ("X", "O") for cell in board))

	def test_print_board_renders_all_cells(self):
		self.ttt.board = ["X", "O", " "] * 3
		buffer = io.StringIO()
		with contextlib.redirect_stdout(buffer):
			self.ttt.print_board()
		output = buffer.getvalue()
		self.assertIn("X", output)
		self.assertIn("O", output)
		self.assertEqual(output.count("---+---+---"), 2)


if __name__ == "__main__":
	unittest.main()
