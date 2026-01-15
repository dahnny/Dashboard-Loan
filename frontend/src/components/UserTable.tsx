import type { User } from "../types";

interface UserTableProps {
  users: User[];
}

export function UserTable({ users }: UserTableProps) {
  return (
    <div className="table">
      <div className="table-row header">
        <div>ID</div>
        <div>Email</div>
        <div>Phone</div>
        <div>Created</div>
      </div>
      {users.map((user) => (
        <div key={user.id} className="table-row">
          <div className="mono">{user.id.slice(0, 8)}</div>
          <div>{user.email}</div>
          <div>{user.phone_number ?? "-"}</div>
          <div>{new Date(user.created_at).toLocaleDateString()}</div>
        </div>
      ))}
      {users.length === 0 && (
        <div className="table-empty">No users found.</div>
      )}
    </div>
  );
}
