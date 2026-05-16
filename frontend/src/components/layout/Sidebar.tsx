import { NavMenu } from './NavMenu';
import type { UserRole } from '@/types';

interface SidebarProps {
  role: UserRole;
}

export function Sidebar({ role }: SidebarProps) {
  return (
    <aside className="sidebar">
      <NavMenu role={role} className="nav-menu--sidebar" />
    </aside>
  );
}
