import React, { useState } from 'react';
import Board from './Board';

// オセロのゲームロジックを実装
function calculateWinner(squares) {
    // 勝利パターンの組み合わせ
    const lines = [
      [0, 1, 2], // 横一列
      [3, 4, 5],
      [6, 7, 8],
      [0, 3, 6], // 縦一列
      [1, 4, 7],
      [2, 5, 8],
      [0, 4, 8], // 斜め
      [2, 4, 6]
    ];
  
    // 各組み合わせについて勝利条件をチェック
    for (let i = 0; i < lines.length; i++) {
      const [a, b, c] = lines[i];
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a]; // 勝者 (X または O) を返す
      }
    }
    return null; // 勝者なし
  }
function Game() {
  // 盤面の状態を管理
  const [squares, setSquares] = useState(Array(9).fill(null)); // 盤面は9マス
  const [xIsNext, setXIsNext] = useState(true); // どちらのプレイヤーのターンか

  // マスがクリックされたときの処理
  const handleClick = (i) => {
    // 盤面のコピーを作成
    const newSquares = squares.slice();
    // すでにマスが埋まっている場合は何もしない
    if (newSquares[i]) {
      return;
    }
    // プレイヤーの石を配置
    newSquares[i] = xIsNext ? 'X' : 'O';
    // 盤面を更新
    setSquares(newSquares);
    // ターンを交代
    setXIsNext(!xIsNext);
  };

  // 勝者を判定
  const winner = calculateWinner(squares);
  let status;
  if (winner) {
    status = 'Winner: ' + winner;
  } else {
    status = 'Next player: ' + (xIsNext ? 'X' : 'O');
  }

  return (
    <div className="game">
      <div className="game-board">
        <Board squares={squares} onClick={handleClick} />
      </div>
      <div className="game-info">{status}</div>
    </div>
  );
}

export default Game;
