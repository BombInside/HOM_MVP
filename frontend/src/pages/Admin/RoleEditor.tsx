import { useEffect, useState } from "react";
import api from "../../api";

type Role = { id: number; name: string; description?: string | null; permissions: string[] };

const RoleEditor = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [perms, setPerms] = useState<string>("");

  const fetchRoles = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<Role[]>("/adminpanel/roles");
      setRoles(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load roles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const addRole = async () => {
    try {
      await api.post("/adminpanel/roles", {
        name,
        description: desc || null,
        permissions: perms.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setName("");
      setDesc("");
      setPerms("");
      await fetchRoles();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Create failed");
    }
  };

  const updateRole = async (id: number, role: Role) => {
    try {
      await api.put(`/adminpanel/roles/${id}`, {
        name: role.name,
        description: role.description,
        permissions: role.permissions,
      });
      await fetchRoles();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Update failed");
    }
  };

  const deleteRole = async (id: number) => {
    if (!confirm("Delete role?")) return;
    try {
      await api.delete(`/adminpanel/roles/${id}`);
      await fetchRoles();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Roles</h1>

      <div className="mb-6 p-4 border rounded dark:border-gray-700">
        <h2 className="font-semibold mb-2">Create Role</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input
            className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
            placeholder="Description"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
          <input
            className="px-3 py-2 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
            placeholder="Permissions (comma-separated)"
            value={perms}
            onChange={(e) => setPerms(e.target.value)}
          />
        </div>
        <button className="mt-3 px-4 py-2 bg-green-600 text-white rounded" onClick={addRole}>
          Add
        </button>
      </div>

      <div className="border rounded dark:border-gray-700 overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Description</th>
              <th className="px-3 py-2">Permissions</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-3 py-2">Loading...</td></tr>
            ) : error ? (
              <tr><td colSpan={5} className="px-3 py-2 text-red-500">{error}</td></tr>
            ) : roles.length === 0 ? (
              <tr><td colSpan={5} className="px-3 py-2">No roles</td></tr>
            ) : (
              roles.map((r) => (
                <tr key={r.id} className="border-t dark:border-gray-800">
                  <td className="px-3 py-2">{r.id}</td>
                  <td className="px-3 py-2">
                    <input
                      className="w-full px-2 py-1 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
                      value={r.name}
                      onChange={(e) => setRoles((prev) => prev.map(x => x.id === r.id ? { ...x, name: e.target.value } : x))}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      className="w-full px-2 py-1 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
                      value={r.description || ""}
                      onChange={(e) => setRoles((prev) => prev.map(x => x.id === r.id ? { ...x, description: e.target.value } : x))}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      className="w-full px-2 py-1 rounded border dark:border-gray-700 bg-white dark:bg-gray-900"
                      value={r.permissions.join(", ")}
                      onChange={(e) => setRoles((prev) => prev.map(x => x.id === r.id ? { ...x, permissions: e.target.value.split(",").map(s=>s.trim()).filter(Boolean) } : x))}
                    />
                  </td>
                  <td className="px-3 py-2 flex gap-2">
                    <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={() => updateRole(r.id, r)}>Save</button>
                    <button className="px-3 py-1 bg-red-600 text-white rounded" onClick={() => deleteRole(r.id)}>Delete</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RoleEditor;
