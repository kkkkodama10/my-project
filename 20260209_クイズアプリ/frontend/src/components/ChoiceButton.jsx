import styles from './ChoiceButton.module.css'

export default function ChoiceButton({ choice, selected, correct, incorrect, disabled, onClick }) {
  const classNames = [
    styles.btn,
    selected ? styles.selected : '',
    disabled ? styles.disabled : '',
    correct ? styles.correct : '',
    incorrect ? styles.incorrect : '',
  ].filter(Boolean).join(' ')

  return (
    <button
      className={classNames}
      disabled={disabled}
      onClick={() => onClick?.(choice.choice_index)}
    >
      {choice.text}
    </button>
  )
}
