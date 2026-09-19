import { PHONE_HINT, phonePlaceholder, sanitizePhoneInput } from '../lib/phone'

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

/**
 * Mismo campo y mismo error en el alta y en «Ya estoy en la lista de espera».
 * El código de país es parte del campo, no una etiqueta fija: el local solo
 * decide con qué prefijo llega rellenado, y quien tenga un número extranjero lo
 * corrige sin salir del formulario.
 */
export default function PhoneField({
  id, value, prefix, error, label = 'Teléfono', hint = PHONE_HINT, autoFocus, onChange,
}: Props) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className={`phone-input${error ? ' has-error' : ''}`}>
        <input
          id={id}
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          maxLength={24}
          placeholder={phonePlaceholder(prefix)}
          value={value}
          autoFocus={autoFocus}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          onChange={(event) => onChange(sanitizePhoneInput(event.target.value))}
        />
      </div>
      {hint && !error && <p id={`${id}-hint`} className="hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="field-error" role="alert">{error}</p>}
    </div>
  )
}
