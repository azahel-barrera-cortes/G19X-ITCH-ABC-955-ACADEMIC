import Boton from '../components/ui/Boton.jsx'

export default function UsuarioInactivo({ onCerrarSesion }) {
  return (
    <main className="flex min-h-full items-center justify-center bg-slate-50 px-6">
      <section className="w-full max-w-md rounded-2xl border border-red-100 bg-white p-8 text-center shadow-sm">
        <div
          className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-2xl text-red-600"
          aria-hidden="true"
        >
          !
        </div>
        <h1 className="mt-5 text-xl font-bold text-slate-900">
          Usuario inactivo
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Tu cuenta está inactiva. Comunícate con tu administrador para recuperar
          el acceso al sistema.
        </p>
        <Boton
          variante="peligro"
          className="mt-6 w-full"
          onClick={onCerrarSesion}
        >
          Cerrar sesión
        </Boton>
      </section>
    </main>
  )
}
