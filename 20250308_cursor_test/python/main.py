from colorama import init, Fore, Style

init()  # coloramaの初期化

def print_board(board):
    """
    ゲームボードの現在の状態を表示する

    Args:
        board (list): 9つのマス目の状態を表すリスト。各要素は "X"、"O" または空白文字 " " のいずれか。
    """
    for i in range(3):
        # Xは赤、Oは青で表示
        print(f" {Fore.RED if board[i*3] == 'X' else Fore.BLUE if board[i*3] == 'O' else ''}{board[i*3]}{Style.RESET_ALL} | "
              f"{Fore.RED if board[i*3+1] == 'X' else Fore.BLUE if board[i*3+1] == 'O' else ''}{board[i*3+1]}{Style.RESET_ALL} | "
              f"{Fore.RED if board[i*3+2] == 'X' else Fore.BLUE if board[i*3+2] == 'O' else ''}{board[i*3+2]}{Style.RESET_ALL} ")
        if i < 2:
            print("-----------")

def check_winner(board):
    """
    ゲームボードの勝者を判定する

    Args:
        board (list): 9つのマス目の状態を表すリスト

    Returns:
        str or None: 勝者のシンボル("X" または "O")。勝者がいない場合はNone。
    """
    # 横のチェック
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != " ":
            return board[i]
    
    # 縦のチェック 
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != " ":
            return board[i]
    
    # 斜めのチェック
    if board[0] == board[4] == board[8] != " ":
        return board[0]
    if board[2] == board[4] == board[6] != " ":
        return board[2]
    
    return None

def main():
    """
    三目並べゲームのメイン処理を実行する
    
    プレイヤーが交互に手を打ち、勝敗が決まるまでまたは引き分けになるまでゲームを続ける
    """
    board = [" " for _ in range(9)]
    current_player = "X"
    
    print("三目並べを開始します!")
    print("マス目は1-9の数字で指定してください:")
    print(" 1 | 2 | 3 ")
    print("-----------")
    print(" 4 | 5 | 6 ")
    print("-----------")
    print(" 7 | 8 | 9 ")
    print(f"\n{Fore.RED}プレイヤーX{Style.RESET_ALL}と{Fore.BLUE}プレイヤーO{Style.RESET_ALL}で対戦します")
    
    while True:
        print_board(board)
        print(f"プレイヤー {Fore.RED if current_player == 'X' else Fore.BLUE}{current_player}{Style.RESET_ALL} の番です")
        
        while True:
            try:
                position = int(input("マス目を選んでください (1-9): ")) - 1
                if 0 <= position <= 8 and board[position] == " ":
                    break
                print("無効な入力です。空いているマス目を選んでください。")
            except ValueError:
                print("1-9の数字を入力してください。")
        
        board[position] = current_player
        
        winner = check_winner(board)
        if winner:
            print_board(board)
            print(f"プレイヤー {Fore.RED if winner == 'X' else Fore.BLUE}{winner}{Style.RESET_ALL} の勝利です!")
            break
        
        if " " not in board:
            print_board(board)
            print("引き分けです!")
            break
        
        current_player = "O" if current_player == "X" else "X"

if __name__ == "__main__":
    main()
