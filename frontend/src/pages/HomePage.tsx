import { Link } from 'react-router-dom';
import { GoldOrbs } from '@/components/GoldOrbs';
import { LeadForm } from '@/components/LeadForm';
import { useLiveMetrics } from '@/hooks/use-live-metrics';

/** Главная: бренд, короткая мысль и форма заявки. */
export function HomePage() {
  useLiveMetrics();

  return (
    <main className="relative min-h-screen overflow-hidden px-5 pb-24 pt-10 sm:px-8 lg:px-12">
      <GoldOrbs />

      <header className="relative z-10 mx-auto max-w-5xl animate-rise">
        <div className="flex justify-end">
          <Link
            to="/admin"
            className="text-xs uppercase tracking-[0.2em] text-mist/40
              transition hover:text-gold-300"
          >
            Админ
          </Link>
        </div>
        <p className="font-display text-5xl leading-none tracking-[0.04em] text-gold-100 sm:text-7xl lg:text-8xl">
          Autéllo Barskiy
        </p>
        <p className="mt-6 max-w-xl font-display text-2xl italic text-gold-200/80 sm:text-3xl">
          Закрытый контур заявки для тёплых клиентов
        </p>
        <p className="mt-4 max-w-lg text-sm leading-relaxed text-mist/65 sm:text-base">
          Заполните поля ниже. Услуги и границы бюджета подгружаются с сервера.
        </p>
        <div className="mt-10 h-px w-full bg-gradient-to-r from-gold-400/50 via-gold-200/20 to-transparent" />
      </header>

      <div className="relative z-10 mx-auto mt-12 max-w-5xl">
        <LeadForm />
      </div>
    </main>
  );
}
