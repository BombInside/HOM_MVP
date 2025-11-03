import { NavLink } from "react-router-dom";

const Sidebar = () => {
  const base = "block px-4 py-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700";
  const active = "bg-gray-200 dark:bg-gray-700 font-semibold";
  return (
    <aside className="w-64 min-h-screen border-r border-gray-200 dark:border-gray-800 p-4">
      <div className="text-xl font-bold mb-6">H.O.M.</div>
      <nav className="flex flex-col gap-1">
        <NavLink to="/dashboard" className={({isActive}) => `${base} ${isActive ? active : ""}`}>Dashboard</NavLink>
        <NavLink to="/machines" className={({isActive}) => `${base} ${isActive ? active : ""}`}>Machines</NavLink>
        <NavLink to="/admin/roles" className={({isActive}) => `${base} ${isActive ? active : ""}`}>Roles</NavLink>
        <NavLink to="/admin/users" className={({isActive}) => `${base} ${isActive ? active : ""}`}>Users</NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;
