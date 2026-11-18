import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { ApplicationsPanel } from '@/components/admin/ApplicationsPanel';
import { ServiceEditor } from '@/components/admin/ServiceEditor';
import { StatsPanel } from '@/components/admin/StatsPanel';
import { GoldOrbs } from '@/components/GoldOrbs';
import { useAuth } from '@/hooks/use-auth';

type TAdminTab = 'services' | 'applications' | 'stats';

/** Защищённая панель: услуги, заявки и статистика. */
export function AdminPanelPage() {
  const { admin, loading, isAuthenticated, logout } = useAuth();
  const [tab, setTab] = useState<TAdminTab>('applications');

  if (loading) {
    return (
      <main className="relative min-h-screen px-5 pt-16 text-mist/60">
        <GoldOrbs />
        <p className="relative z-10">Проверка сессии…</p>
      </main>
    );
  }

  if (!isAuthenticated || !admin) {
    return <Navigate to="/admin/login" replace />;
  }

  return (
    <main className="relative min-h-screen px-5 pb-16 pt-8 sm:px-8 lg:px-12">
      <GoldOrbs />

      <header className="relative z-10 mx-auto flex max-w-6xl flex-col gap-3
        sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-display text-3xl text-gold-100 sm:text-4xl">
            Autéllo Admin
          </p>
          <p className="mt-1 text-sm text-mist">
            Вы вошли как <span className="text-gold-200">{admin.login}</span>
          </p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link to="/" className="text-mist hover:text-gold-200">
            На сайт
          </Link>
          <button
            type="button"
            onClick={logout}
            className="text-gold-300 hover:underline"
          >
            Выйти
          </button>
        </div>
      </header>

      <nav className="relative z-10 mx-auto mt-6 flex max-w-6xl flex-wrap gap-4">
        <TabButton
          active={tab === 'applications'}
          label="Заявки"
          onClick={() => setTab('applications')}
        />
        <TabButton
          active={tab === 'services'}
          label="Услуги"
          onClick={() => setTab('services')}
        />
        <TabButton
          active={tab === 'stats'}
          label="Статистика"
          onClick={() => setTab('stats')}
        />
      </nav>

      <div className="relative z-10 mx-auto mt-6 max-w-6xl">
        <AdminTabContent tab={tab} />
      </div>
    </main>
  );
}

interface IAdminTabContentProps {
  tab: TAdminTab;
}

function AdminTabContent({ tab }: IAdminTabContentProps) {
  if (tab === 'applications') {
    return <ApplicationsPanel />;
  }
  if (tab === 'services') {
    return <ServiceEditor />;
  }
  return <StatsPanel />;
}

interface ITabButtonProps {
  active: boolean;
  label: string;
  onClick: () => void;
}

function TabButton({ active, label, onClick }: ITabButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? 'border-b border-gold-300 pb-2 text-sm uppercase tracking-[0.16em] text-gold-100'
          : 'border-b border-transparent pb-2 text-sm uppercase tracking-[0.16em] text-mist hover:text-gold-200'
      }
    >
      {label}
    </button>
  );
}
