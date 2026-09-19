type Props = { offline: boolean }

/** El wifi de la puerta es malo: se avisa del reintento sin borrar lo último que se vio. */
export default function ConnectionBanner({ offline }: Props) {
  if (!offline) return null
  return (
    <p className="banner banner-offline" role="status">
      Sin conexión. Seguimos intentando y mantenemos lo último que vimos.
    </p>
  )
}
