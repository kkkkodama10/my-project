import React, { useState } from 'react';
import Board from './Board';

// オセロのゲームロジックを実装
function calculateWinner(squares) {
  // ここに勝敗判定のロジックを実装（省略）
  return null; // 現状では勝者はいない
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
