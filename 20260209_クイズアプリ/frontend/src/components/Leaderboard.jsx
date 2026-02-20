import styles from './Leaderboard.module.css'

export default function Leaderboard({ data }) {
  const { leaderboard = [], event_summary } = data || {}

  return (
    <div>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>順位</th>
            <th>名前</th>
            <th>正解数</th>
            <th>未回答</th>
            <th>正答率</th>
            <th>回答時間合計</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map(entry => (
            <tr key={entry.rank}>
              <td>{entry.rank}</td>
              <td>{entry.display_name}</td>
              <td>{entry.correct_count}</td>
              <td>{entry.unanswered_count ?? '-'}</td>
              <td>{(entry.accuracy * 100).toFixed(0)}%</td>
              <td>{entry.correct_time_sum_sec_1dp}s</td>
            </tr>
          ))}
        </tbody>
      </table>
      {event_summary && (
        <p className={styles.summary}>
          全{event_summary.total_questions}問 / 終了: {event_summary.finished_at || '-'}
        </p>
      )}
    </div>
  )
}
