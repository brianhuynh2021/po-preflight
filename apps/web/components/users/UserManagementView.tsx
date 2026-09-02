"use client";

import React, { useEffect, useState } from "react";
import { api, describeError } from "@/app/lib/api/client";
import type { UserAccount, CreateUserPayload } from "@/app/lib/api/types";
import { ROLE_LABEL_VI, type UserRole } from "@/app/lib/types";

const ROLE_BADGE_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  admin: { bg: "bg-purple-500/10 dark:bg-purple-500/20", text: "text-purple-700 dark:text-purple-300", border: "border-purple-200 dark:border-purple-800" },
  director: { bg: "bg-indigo-500/10 dark:bg-indigo-500/20", text: "text-indigo-700 dark:text-indigo-300", border: "border-indigo-200 dark:border-indigo-800" },
  manager: { bg: "bg-blue-500/10 dark:bg-blue-500/20", text: "text-blue-700 dark:text-blue-300", border: "border-blue-200 dark:border-blue-800" },
  sales_admin: { bg: "bg-emerald-500/10 dark:bg-emerald-500/20", text: "text-emerald-700 dark:text-emerald-300", border: "border-emerald-200 dark:border-emerald-800" },
  auditor: { bg: "bg-amber-500/10 dark:bg-amber-500/20", text: "text-amber-700 dark:text-amber-300", border: "border-amber-200 dark:border-amber-800" },
  viewer: { bg: "bg-stone-500/10 dark:bg-stone-500/20", text: "text-stone-700 dark:text-stone-300", border: "border-stone-200 dark:border-stone-800" },
};

const DEFAULT_USERS_SEED: UserAccount[] = [
  { id: 1, org_id: "default", username: "admin", display_name: "Hệ Thống Quản Trị", email: "admin@preflight.vn", role: "admin", is_active: true, created_at: "2026-09-01T00:00:00Z" },
  { id: 2, org_id: "default", username: "director", display_name: "Giám Đốc Phê Duyệt", email: "director@preflight.vn", role: "director", is_active: true, created_at: "2026-09-01T00:00:00Z" },
  { id: 3, org_id: "default", username: "manager", display_name: "Trưởng Phòng Vận Hành", email: "manager@preflight.vn", role: "manager", is_active: true, created_at: "2026-09-01T00:00:00Z" },
  { id: 4, org_id: "default", username: "sales_admin", display_name: "Nhân Viên Sales Admin", email: "sales@preflight.vn", role: "sales_admin", is_active: true, created_at: "2026-09-01T00:00:00Z" },
  { id: 5, org_id: "default", username: "auditor", display_name: "Kiểm Toán Viên", email: "auditor@preflight.vn", role: "auditor", is_active: true, created_at: "2026-09-01T00:00:00Z" },
  { id: 6, org_id: "default", username: "viewer", display_name: "Người Xem Báo Cáo", email: "viewer@preflight.vn", role: "viewer", is_active: true, created_at: "2026-09-01T00:00:00Z" },
];

export function UserManagementView() {
  const [users, setUsers] = useState<UserAccount[]>(DEFAULT_USERS_SEED);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [newUser, setNewUser] = useState<CreateUserPayload>({
    username: "",
    display_name: "",
    email: "",
    password: "",
    role: "sales_admin",
  });

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.users.list();
      if (Array.isArray(data) && data.length > 0) {
        setUsers(data);
      }
    } catch {
      // Fallback to local default seed
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    api.users
      .list()
      .then((data) => {
        if (!ignore && Array.isArray(data) && data.length > 0) {
          setUsers(data);
        }
      })
      .catch(() => {
        // Fallback to seed
      });
    return () => {
      ignore = true;
    };
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUser.username || !newUser.password || !newUser.display_name) {
      setError("Vui lòng điền đầy đủ thông tin người dùng.");
      return;
    }
    try {
      await api.users.create(newUser);
      setSuccessMsg(`Đã tạo thành công người dùng '${newUser.username}'.`);
      setShowCreateModal(false);
      setNewUser({ username: "", display_name: "", email: "", password: "", role: "sales_admin" });
      loadUsers();
    } catch (err) {
      setError(describeError(err));
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showResetModal || !newPassword) return;
    try {
      await api.users.resetPassword(showResetModal, newPassword);
      setSuccessMsg(`Đã đặt lại mật khẩu thành công cho '${showResetModal}'.`);
      setShowResetModal(null);
      setNewPassword("");
    } catch (err) {
      setError(describeError(err));
    }
  };

  const handleUnlock = async (username: string) => {
    try {
      await api.users.unlock(username);
      setSuccessMsg(`Đã mở khóa tài khoản '${username}'.`);
      loadUsers();
    } catch (err) {
      setError(describeError(err));
    }
  };

  const handleDelete = async (username: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa người dùng '${username}'?`)) return;
    try {
      await api.users.delete(username);
      setSuccessMsg(`Đã xóa người dùng '${username}'.`);
      loadUsers();
    } catch (err) {
      setError(describeError(err));
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.display_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === "all" || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const totalUsers = users.length;
  const adminDirectorCount = users.filter((u) => u.role === "admin" || u.role === "director").length;
  const managerCount = users.filter((u) => u.role === "manager").length;
  const lockedCount = users.filter((u) => Boolean(u.locked_until)).length;

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Quản lý Người dùng & Ma trận Phê duyệt</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Thiết lập tài khoản người dùng, phân quyền RBAC đa cấp và ma trận duyệt tự động theo giá trị đơn hàng.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg text-sm shadow-sm hover:opacity-90 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            Tạo người dùng mới
          </button>
        </div>
      </div>

      {/* Feedback alerts */}
      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">&times;</button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-300 text-sm flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="font-bold">&times;</button>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-card border border-border">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Tổng người dùng</div>
          <div className="text-2xl font-bold text-foreground mt-2">{totalUsers}</div>
          <div className="text-xs text-muted-foreground mt-1">6 vai trò hệ thống chuẩn</div>
        </div>
        <div className="p-4 rounded-xl bg-card border border-border">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quản trị & Giám đốc</div>
          <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-2">{adminDirectorCount}</div>
          <div className="text-xs text-muted-foreground mt-1">Quyền duyệt &gt; 50M &amp; Ngoại lệ</div>
        </div>
        <div className="p-4 rounded-xl bg-card border border-border">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Trưởng phòng (Manager)</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">{managerCount}</div>
          <div className="text-xs text-muted-foreground mt-1">Quyền duyệt đơn &le; 50.000.000 đ</div>
        </div>
        <div className="p-4 rounded-xl bg-card border border-border">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Tài khoản bị khóa</div>
          <div className={`text-2xl font-bold mt-2 ${lockedCount > 0 ? "text-red-600" : "text-emerald-600 dark:text-emerald-400"}`}>
            {lockedCount}
          </div>
          <div className="text-xs text-muted-foreground mt-1">Tự khóa sau 5 lần sai pass</div>
        </div>
      </div>

      {/* Approval Matrix SOX 404 Guide Card */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-blue-500/5 via-indigo-500/5 to-purple-500/5 border border-border">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h3 className="font-semibold text-sm text-foreground">Ma trận Phê duyệt &amp; Quy tắc Phân tách Trách nhiệm (SoD)</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-muted-foreground mt-2">
          <div className="p-2.5 rounded-lg bg-background/80 border border-border/60">
            <span className="font-medium text-foreground block mb-1">Đơn hàng &le; 50.000.000 đ:</span>
            Yêu cầu cấp tối thiểu <strong className="text-blue-600 dark:text-blue-400">Trưởng phòng (Manager)</strong> phê duyệt.
          </div>
          <div className="p-2.5 rounded-lg bg-background/80 border border-border/60">
            <span className="font-medium text-foreground block mb-1">Đơn hàng &gt; 50.000.000 đ hoặc Vượt hạn mức:</span>
            Yêu cầu cấp tối thiểu <strong className="text-indigo-600 dark:text-indigo-400">Giám đốc (Director)</strong> phê duyệt.
          </div>
          <div className="p-2.5 rounded-lg bg-background/80 border border-border/60">
            <span className="font-medium text-foreground block mb-1">Quy tắc Phân tách Trách nhiệm (SoD):</span>
            Người tạo/upload đơn <strong className="text-red-600 dark:text-red-400">không được tự duyệt</strong> đơn của chính mình.
          </div>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <input
            type="text"
            placeholder="Tìm theo username, tên, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <svg className="w-4 h-4 text-muted-foreground absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <label className="text-xs text-muted-foreground whitespace-nowrap">Lọc theo vai trò:</label>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="text-sm bg-background border border-border rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">Tất cả vai trò</option>
            <option value="admin">Quản trị hệ thống (Admin)</option>
            <option value="director">Giám đốc phê duyệt (Director)</option>
            <option value="manager">Trưởng phòng (Manager)</option>
            <option value="sales_admin">Sales Admin</option>
            <option value="auditor">Kiểm toán viên (Auditor)</option>
            <option value="viewer">Người xem (Viewer)</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/40 text-muted-foreground text-xs font-semibold uppercase tracking-wider border-b border-border">
              <tr>
                <th className="px-4 py-3">Người dùng</th>
                <th className="px-4 py-3">Vai trò</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Thất bại</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    Đang tải danh sách người dùng...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    Không tìm thấy người dùng phù hợp.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => {
                  const badge = ROLE_BADGE_STYLE[u.role] || ROLE_BADGE_STYLE.viewer;
                  const isLocked = Boolean(u.locked_until);
                  return (
                    <tr key={u.username} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-foreground">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                            {u.username.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold">{u.display_name}</div>
                            <div className="text-xs text-muted-foreground font-mono">@{u.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${badge.bg} ${badge.text} ${badge.border}`}>
                          {ROLE_LABEL_VI[u.role as UserRole] || u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{u.email}</td>
                      <td className="px-4 py-3">
                        {isLocked ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/50">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                            Bị khóa
                          </span>
                        ) : u.is_active ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            Hoạt động
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-stone-500/10 text-stone-600 border border-stone-200">
                            Vô hiệu
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-muted-foreground">
                        {u.failed_attempts || 0}/5 lần
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isLocked && (
                            <button
                              onClick={() => handleUnlock(u.username)}
                              className="px-2 py-1 text-xs font-medium text-amber-600 hover:bg-amber-500/10 rounded transition-colors"
                            >
                              Mở khóa
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setShowResetModal(u.username);
                              setNewPassword("");
                            }}
                            className="px-2 py-1 text-xs font-medium text-primary hover:bg-primary/10 rounded transition-colors"
                          >
                            Đổi pass
                          </button>
                          {u.username !== "admin" && (
                            <button
                              onClick={() => handleDelete(u.username)}
                              className="px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-500/10 rounded transition-colors"
                            >
                              Xóa
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Create User */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md shadow-lg space-y-4">
            <h2 className="text-lg font-bold text-foreground">Tạo Người Dùng Mới</h2>
            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Tên đăng nhập (Username):</label>
                <input
                  type="text"
                  required
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  placeholder="ví dụ: tran_van_a"
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Họ và tên:</label>
                <input
                  type="text"
                  required
                  value={newUser.display_name}
                  onChange={(e) => setNewUser({ ...newUser, display_name: e.target.value })}
                  placeholder="ví dụ: Trần Văn A"
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Email:</label>
                <input
                  type="email"
                  required
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="email@preflight.vn"
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Mật khẩu khởi tạo (Argon2id):</label>
                <input
                  type="password"
                  required
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="Tối thiểu 8 ký tự, gồm chữ & số"
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Vai trò hệ thống:</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="sales_admin">Sales Admin (Tạo đơn &amp; Yêu cầu sửa)</option>
                  <option value="manager">Trưởng phòng - Manager (Duyệt đơn &le; 50M)</option>
                  <option value="director">Giám đốc - Director (Duyệt đơn &gt; 50M)</option>
                  <option value="auditor">Kiểm toán viên (Xem &amp; Xuất báo cáo)</option>
                  <option value="viewer">Người xem (Viewer)</option>
                  <option value="admin">Quản trị hệ thống (Admin)</option>
                </select>
              </div>
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted rounded-lg transition-colors"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-colors shadow-sm"
                >
                  Tạo tài khoản
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Reset Password */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md shadow-lg space-y-4">
            <h2 className="text-lg font-bold text-foreground">Đặt Lại Mật Khẩu</h2>
            <p className="text-sm text-muted-foreground">
              Đổi mật khẩu cho người dùng <strong className="text-foreground font-mono">@{showResetModal}</strong>.
            </p>
            <form onSubmit={handleResetPassword} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Mật khẩu mới:</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Tối thiểu 8 ký tự, gồm chữ & số"
                  className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowResetModal(null)}
                  className="px-4 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted rounded-lg transition-colors"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-colors shadow-sm"
                >
                  Cập nhật mật khẩu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
