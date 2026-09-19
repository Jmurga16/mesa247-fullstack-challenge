type Props = {
  id: string
  value: string
  prefix: string
  error?: string
  label?: string
  hint?: string
  autoFocus?: boolean
  onChange: (value: string) => void
}

/** Mismo campo y mismo error en el alta y en «Ya estoy en la lista de espera». */
export default function PhoneField({
  id, value, prefix, error, label = 'Teléfono', hint, autoFocus, onChange,
}: Props) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className={`phone-input${error ? ' has-error' : ''}`}>
        <span className="phone-prefix">{prefix}</span>
        <input
          id={id}
          type="tel"
          inputMode="tel"
          autoComplete="tel-national"
          placeholder="987 654 321"
          value={value}
          autoFocus={autoFocus}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
      {hint && !error && <p id={`${id}-hint`} className="hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="field-error" role="alert">{error}</p>}
    </div>
  )
}
