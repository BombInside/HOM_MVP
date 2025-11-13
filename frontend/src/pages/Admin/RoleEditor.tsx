import { useEffect, useState, FormEvent } from "react";
import api from "../../api"; 
import { useTranslation } from "react-i18next";
import { Trash2, Save, Plus, X, Shield, Lock, SquarePen } from "lucide-react";

// --- Типы данных ---

type Permission = {
  id: number;
  code: string;
  description?: string | null;
};

type Role = {
  id: number;
  name: string;
  description?: string | null;
  permissions: Permission[];
};

type RoleCreate = {
  name: string;
  description: string | null;
  permission_codes: string[];
};

type RoleUpdateInput = {
  name?: string | null;
  description?: string | null;
  permission_codes?: string[] | null;
};

// --- Основной компонент ---

const RoleEditor = () => {
  const { t } = useTranslation();
  
  // Состояния для данных
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Состояния для формы создания
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [selectedNewPerms, setSelectedNewPerms] = useState<string[]>([]);
  
  // Состояние модального окна удаления
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [roleToDelete, setRoleToDelete] = useState<Role | null>(null);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      // API endpoints for roles and permissions:
      const [rolesRes, permsRes] = await Promise.all([
        api.get<Role[]>("/adminpanel/roles"),
        api.get<Permission[]>("/adminpanel/permissions"),
      ]);
      
      // Обрабатываем роли (API возвращает объекты Permission, что соответствует RoleOut)
      setRoles(rolesRes.data);
      setAllPermissions(permsRes.data);

    } catch (e: any) {
      const msg = e?.response?.data?.detail || t("roles.loading_failed");
      setError(msg);
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // В React 18 useEffect запускается дважды в dev режиме, но это не проблема.
    fetchAllData();
  }, [t]);

  // --- Handlers ---
  
  // Добавление новой роли
  const handleAddRole = async (e: FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    const codes = selectedNewPerms.filter(Boolean);
    const data: RoleCreate = {
      name: newName.trim(),
      description: newDesc.trim() || null,
      permission_codes: codes,
    };

    try {
      await api.post("/adminpanel/roles", data);
      // Очистка формы
      setNewName("");
      setNewDesc("");
      setSelectedNewPerms([]);
      await fetchAllData();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("roles.create_failed"));
    }
  };

  // Сохранение изменений в существующей роли
  const handleUpdateRole = async (role: Role) => {
    // Подготовка данных для отправки
    const codes = role.permissions.map(p => p.code).filter(Boolean);
    const updateData: RoleUpdateInput = {
      name: role.name,
      description: role.description,
      permission_codes: codes,
    };

    try {
      await api.put(`/adminpanel/roles/${role.id}`, updateData);
      await fetchAllData();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("roles.save_failed"));
    }
  };
  
  // Обработка удаления
  const confirmDelete = (role: Role) => {
    setRoleToDelete(role);
    setIsModalOpen(true);
  }
  
  const handleDeleteRole = async () => {
    if (!roleToDelete) return;
    const id = roleToDelete.id;
    setRoleToDelete(null);
    setIsModalOpen(false);

    try {
      await api.delete(`/adminpanel/roles/${id}`);
      await fetchAllData();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("roles.delete_failed"));
    }
  };

  // Изменение состояния выбора прав в таблице
  const togglePermission = (roleId: number, code: string, isChecked: boolean) => {
    setRoles(prevRoles => prevRoles.map(r => {
      if (r.id !== roleId) return r;
      
      // Находим объект права из общего списка (allPermissions)
      let updatedPermissions: Permission[] = r.permissions.map(p => p);
      const permObj = allPermissions.find(p => p.code === code);

      if (isChecked && permObj) {
        // Добавить право, если его нет
        if (!updatedPermissions.some(p => p.code === code)) {
          updatedPermissions.push(permObj);
        }
      } else if (!isChecked) {
        // Удалить право
        updatedPermissions = updatedPermissions.filter(p => p.code !== code);
      }
      
      // Сортировка для стабильности
      updatedPermissions.sort((a, b) => a.code.localeCompare(b.code));
      
      return { ...r, permissions: updatedPermissions };
    }));
  };

  // Изменение состояния выбора прав для формы создания
  const toggleNewPermission = (code: string, isChecked: boolean) => {
    setSelectedNewPerms(prevCodes => isChecked
        ? [...prevCodes, code]
        : prevCodes.filter(c => c !== code)
    );
  };
  
  // Исключаем роль 'Admin' из редактирования
  const listToDisplay = roles.filter(r => r.name !== "Admin"); 
  
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-gray-100">
        {t("roles.title")}
      </h1>

      {/* Форма создания роли */}
      <div className="mb-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-green-500" />
          {t("roles.create")}
        </h2>
        <form onSubmit={handleAddRole} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 w-full"
              placeholder={t("roles.name")}
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
            />
            <input
              className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 w-full md:col-span-2"
              placeholder={t("roles.description")}
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
            />
          </div>

          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="font-medium mb-3">{t("roles.permissions")}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {allPermissions.map((perm) => (
                <label key={perm.code} className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    className="form-checkbox h-4 w-4 text-sky-600 dark:text-sky-400 rounded"
                    checked={selectedNewPerms.includes(perm.code)}
                    onChange={(e) => toggleNewPermission(perm.code, e.target.checked)}
                  />
                  <span>{perm.code}</span>
                  {perm.description && (
                    <span className="text-gray-500 dark:text-gray-400 text-xs">({perm.description})</span>
                  )}
                </label>
              ))}
            </div>
          </div>
          
          <button
            type="submit"
            className="w-full md:w-auto px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            {t("roles.add")}
          </button>
        </form>
      </div>

      {/* Таблица ролей */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-1/12">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-2/12">{t("roles.name")}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-2/12">{t("roles.description")}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-6/12">{t("roles.permissions")}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-1/12"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">{t("roles.loading")}</td></tr>
            ) : error ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-red-500">{error}</td></tr>
            ) : listToDisplay.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">{t("roles.no_roles")}</td></tr>
            ) : (
              listToDisplay.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{r.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    <input
                      className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 w-full max-w-xs"
                      value={r.name}
                      onChange={(e) => setRoles(prev => prev.map(x => x.id === r.id ? { ...x, name: e.target.value } : x))}
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-normal text-sm text-gray-500 dark:text-gray-300">
                    <input
                      className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 w-full max-w-xs"
                      value={r.description || ""}
                      onChange={(e) => setRoles(prev => prev.map(x => x.id === r.id ? { ...x, description: e.target.value } : x))}
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-normal text-sm text-gray-500 dark:text-gray-300">
                    <div className="flex flex-wrap gap-x-4 gap-y-1">
                      {allPermissions.map(perm => (
                        <label key={perm.code} className="flex items-center space-x-1 text-xs cursor-pointer">
                          <input
                            type="checkbox"
                            className="form-checkbox h-3 w-3 text-sky-600 dark:text-sky-400 rounded"
                            checked={r.permissions.some(p => p.code === perm.code)}
                            onChange={(e) => togglePermission(r.id, perm.code, e.target.checked)}
                          />
                          <span className="font-mono">{perm.code}</span>
                        </label>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex gap-2">
                      <button 
                        className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-1" 
                        onClick={() => handleUpdateRole(r)}
                      >
                        <Save className="w-4 h-4" />
                      </button>
                      <button 
                        className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-1" 
                        onClick={() => confirmDelete(r)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Модальное окно подтверждения удаления */}
      {isModalOpen && roleToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4 text-red-600 flex items-center gap-2">
                <Trash2 className="w-5 h-5"/>
                {t("roles.confirm_delete_title")}
            </h3>
            <p className="mb-6">
              {t("roles.confirm_delete_message", { roleName: roleToDelete.name })}
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 transition"
                onClick={() => setIsModalOpen(false)}
              >
                {t("roles.cancel")}
              </button>
              <button
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
                onClick={handleDeleteRole}
              >
                {t("roles.delete")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleEditor;