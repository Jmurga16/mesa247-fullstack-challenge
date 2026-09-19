type Props = {
  value: number
  max: number
  error?: string
  onChange: (value: number) => void
}

export default function PartySizeField({ value, max, error, onChange }: Props) {
  const clamp = (next: number) => onChange(Math.min(max, Math.max(1, next)))

  return (
    <div className="field">
      <span className="label" id="party-label">¿Cuántos son?</span>
      <div className="stepper" role="group" aria-labelledby="party-label">
        <button type="button" onClick={() => clamp(value - 1)} disabled={value <= 1} aria-label="Quitar una persona">–</button>
        <output aria-live="polite">{value}</output>
        <button type="button" onClick={() => clamp(value + 1)} disabled={value >= max} aria-label="Agregar una persona">+</button>
      </div>
      <p className="hint">Hasta {max} personas. Para grupos más grandes, habla con el anfitrión.</p>
      {error && <p className="field-error" role="alert">{error}</p>}
    </div>
  )
}
