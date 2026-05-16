import { NavLink } from 'react-router-dom';
import { NAV_BY_ROLE } from '@/config/navigation';
import type { UserRole } from '@/types';

interface NavMenuProps {
  role: UserRole;
  onNavigate?: () => void;
  className?: string;
}

export function NavMenu({ role, onNavigate, className = '' }: NavMenuProps) {
  const items = NAV_BY_ROLE[role];

  return (
    <nav className={`nav-menu ${className}`.trim()} aria-label="Основная навигация">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `nav-menu__link${isActive ? ' nav-menu__link--active' : ''}`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
