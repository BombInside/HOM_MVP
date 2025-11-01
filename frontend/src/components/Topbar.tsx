import { useAppDispatch, useAppSelector } from "../app/store";
import { logout } from "../app/slices/authSlice";
import ThemeToggle from "./ThemeToggle";
import LanguageSwitcher from "./LanguageSwitcher";
import { Link } from "react-router-dom";

const Topbar = () => {
  const user = useAppSelector((s) => s.auth.user);
  const dispatch = useAppDispatch();
  return (
    <header className="w-full flex items-center justify-between border-b border-gray-200 dark:border-gray-800 p-3">
      <div className="flex items-center gap-3">
        <Link to="/" className="text-lg font-semibold">History of Machines</Link>
      </div>
      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <ThemeToggle />
        {user?.email ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-300">{user.email}</span>
            <button className="px-3 py-1 border rounded" onClick={() => dispatch(logout())}>Logout</button>
          </div>
        ) : (
          <Link className="px-3 py-1 border rounded" to="/login">Login</Link>
        )}
      </div>
    </header>
  );
};

export default Topbar;
