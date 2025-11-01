import { useAppSelector, useAppDispatch } from "../app/store";
import { logout } from "../app/slices/authSlice";

const Topbar = () => {
  const { user } = useAppSelector((s) => s.auth);
  const dispatch = useAppDispatch();

  return (
    <div className="flex justify-between items-center px-4 py-2 bg-gray-900 text-white">
      <h1 className="font-semibold text-lg">Admin Panel</h1>
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-sm text-gray-300">
            {user.email} {user.is_admin && "(admin)"}
          </span>
        )}
        <button
          onClick={() => dispatch(logout())}
          className="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-sm"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default Topbar;
