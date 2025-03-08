import React from 'react';

// 盤面の各マスを表すコンポーネント
function Square({ value, onClick }) {
  return (
    <button className="square" onClick={onClick}>
      {value}
    </button>
  );
}

// 盤面全体を表すコンポーネント
function Board({ squares, onClick }) {
  // 盤面のマスを生成
  const renderSquare = (i) => {
    return (
      <Square
        value={squares[i]} // マスの値（'X', 'O', または null）
        onClick={() => onClick(i)} // マスがクリックされたときの処理
      />
    );
  };

  return (
    <div>
      <div className="board-row">
        {renderSquare(0)}
        {renderSquare(1)}
        {renderSquare(2)}
      </div>
      <div className="board-row">
        {renderSquare(3)}
        {renderSquare(4)}
        {renderSquare(5)}
      </div>
      <div className="board-row">
        {renderSquare(6)}
        {renderSquare(7)}
        {renderSquare(8)}
      </div>
    </div>
  );
}

export default Board;
