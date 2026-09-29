import copy
import importlib.util
import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

MODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tic-tac-toe.py")
spec = importlib.util.spec_from_file_location("tic_tac_toe", MODULE_PATH)
ttt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ttt)

ALL_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

# Tie game: X O X / X O O / O X X, no line completed by either player.
TIE_INPUTS = ["1", "2", "3", "5", "4", "6", "8", "7", "9"]
# X wins on the anti-diagonal (squares 3, 5, 7).
ANTI_DIAG_INPUTS = ["3", "1", "5", "2", "7"]


def fresh_board():
    return [" " for _ in range(9)]


def run_game(inputs):
    ttt.board = fresh_board()
    buffer = io.StringIO()
    with patch("builtins.input", side_effect=list(inputs)), redirect_stdout(buffer):
        ttt.play_game()
    return buffer.getvalue(), ttt.board


class HasWinLineTests(unittest.TestCase):
    def setUp(self):
        ttt.board = fresh_board()

    def test_all_eight_lines_win_for_both_players(self):
        for line in ALL_LINES:
            for player in ("X", "O"):
                with self.subTest(line=line, player=player):
                    ttt.board = fresh_board()
                    for index in line:
                        ttt.board[index] = player
                    self.assertTrue(ttt.has_won(player))
                    self.assertFalse(ttt.has_won("O" if player == "X" else "X"))

    def test_anti_diagonal_specifically(self):
        for index in (2, 4, 6):
            ttt.board[index] = "X"
        self.assertTrue(ttt.has_won("X"))

    def test_empty_board_has_no_winner(self):
        self.assertFalse(ttt.has_won("X"))
        self.assertFalse(ttt.has_won("O"))

    def test_single_mark_is_not_a_win(self):
        ttt.board[4] = "X"
        self.assertFalse(ttt.has_won("X"))

    def test_partial_line_is_not_a_win(self):
        ttt.board[2] = "O"
        ttt.board[4] = "O"
        self.assertFalse(ttt.has_won("O"))

    def test_mixed_line_is_not_a_win(self):
        ttt.board[2] = "X"
        ttt.board[4] = "O"
        ttt.board[6] = "X"
        self.assertFalse(ttt.has_won("X"))
        self.assertFalse(ttt.has_won("O"))

    def test_repeated_calls_are_pure_and_deterministic(self):
        for index in (2, 4, 6):
            ttt.board[index] = "O"
        snapshot = copy.deepcopy(ttt.board)
        results = [ttt.has_won("O") for _ in range(5)]
        self.assertEqual(results, [True] * 5)
        self.assertEqual(ttt.board, snapshot)


class PlayGameTests(unittest.TestCase):
    def test_anti_diagonal_win_through_play_game(self):
        output, board = run_game(ANTI_DIAG_INPUTS)
        self.assertIn("Player X wins!", output)
        self.assertEqual(board[2], "X")
        self.assertEqual(board[4], "X")
        self.assertEqual(board[6], "X")

    def test_tie_game(self):
        output, board = run_game(TIE_INPUTS)
        self.assertIn("It's a tie!", output)
        self.assertNotIn("wins!", output)
        self.assertEqual(board, ["X", "O", "X", "X", "O", "O", "O", "X", "X"])

    def test_invalid_inputs_do_not_mutate_state_and_recover(self):
        # Two rejected entries, then valid play resumes and X wins a column.
        output, board = run_game(["abc", "10", "5", "1", "2", "3", "6", "7", "8"])
        self.assertEqual(output.count("Please enter a number from 1 to 9."), 2)
        self.assertEqual(board[4], "X")
        self.assertEqual(len(board), 9)
        self.assertTrue(all(cell in ("X", "O", " ") for cell in board))

    def test_out_of_range_and_blank_inputs_rejected(self):
        output, _ = run_game(["0", "99", "", "x"] + TIE_INPUTS)
        self.assertEqual(output.count("Please enter a number from 1 to 9."), 4)

    def test_failed_call_rolls_back_then_success_unaffected(self):
        ttt.board = fresh_board()
        inputs = ["bogus", "5", "1", "2", "3", "4", "6", "7", "8"]
        snapshots = []

        def fake_input(prompt=""):
            snapshots.append(copy.deepcopy(ttt.board))
            return inputs[len(snapshots) - 1]

        buffer = io.StringIO()
        with patch("builtins.input", side_effect=fake_input), redirect_stdout(buffer):
            ttt.play_game()
        # The turn after the rejected input must observe an untouched board.
        self.assertEqual(snapshots[1], fresh_board())
        # The immediately following valid move succeeds normally.
        self.assertEqual(ttt.board[4], "X")
        self.assertEqual(ttt.board.count("X"), 4)
        self.assertEqual(ttt.board.count("O"), 4)

    def test_same_input_sequence_replays_identically(self):
        output_a, board_a = run_game(TIE_INPUTS)
        output_b, board_b = run_game(TIE_INPUTS)
        self.assertEqual(output_a, output_b)
        self.assertEqual(board_a, board_b)

    def test_consecutive_games_are_deterministic(self):
        results = [run_game(ANTI_DIAG_INPUTS)[0] for _ in range(3)]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertIn("Player X wins!", results[0])

    def test_board_size_stays_bounded_after_many_games(self):
        for _ in range(10):
            run_game(TIE_INPUTS)
        self.assertEqual(len(ttt.board), 9)

    def test_other_lines_still_win_through_play_game(self):
        # X wins top row (squares 1, 2, 3).
        output, _ = run_game(["1", "4", "2", "5", "3"])
        self.assertIn("Player X wins!", output)
        # O wins left column (squares 1, 4, 7).
        output, _ = run_game(["2", "1", "3", "4", "8", "7"])
        self.assertIn("Player O wins!", output)


if __name__ == "__main__":
    unittest.main()
