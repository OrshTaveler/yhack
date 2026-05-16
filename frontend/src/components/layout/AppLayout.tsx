import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ROLE_LABELS } from '@/data/mockAccounts';
import { useAuth } from '@/hooks/useAuth';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { NavMenu } from './NavMenu';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width: 900px)');
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.classList.toggle('nav-open', menuOpen);
    return () => document.body.classList.remove('nav-open');
  }, [menuOpen]);

  if (!user) return null;

  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__start">
          {isMobile && (
            <button
              type="button"
              className="burger"
              aria-expanded={menuOpen}
              aria-controls="mobile-nav"
              aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <span className="burger__bar" />
              <span className="burger__bar" />
              <span className="burger__bar" />
            </button>
          )}
          <div className="app-header__brand">
            <span className="app-header__logo">ПУ</span>
            <div className="app-header__titles">
              <strong className="app-header__app-name">Помощник учителя</strong>
              <span className="app-header__role">{ROLE_LABELS[user.role]}</span>
            </div>
          </div>
        </div>
        <div className="app-header__user">
          <span className="app-header__name">{user.name}</span>
          <button type="button" className="btn btn--ghost btn--sm" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      {isMobile && menuOpen && (
        <button
          type="button"
          className="nav-overlay"
          aria-label="Закрыть меню"
          onClick={closeMenu}
        />
      )}

      <div className="app-body">
        {!isMobile && <Sidebar role={user.role} />}

        {isMobile && (
          <aside
            id="mobile-nav"
            className={`nav-drawer${menuOpen ? ' nav-drawer--open' : ''}`}
            aria-hidden={!menuOpen}
          >
            <div className="nav-drawer__header">
              <span className="nav-drawer__title">Меню</span>
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={closeMenu}
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>
            <NavMenu role={user.role} onNavigate={closeMenu} className="nav-menu--drawer" />
          </aside>
        )}

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
