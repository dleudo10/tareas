export type TaskStatus =
    | "PENDING"
    | "IN_PROGRESS"
    | "COMPLETED";

export interface Category {
    id: number;
    name: string;
    description: string;
}

export interface Task {
    id: number;
    title: string;
    description: string;
    status: TaskStatus;
    category: number;
    category_name: string;
    owner_username: string;
    created_at: string;
    updated_at: string;
}

export interface TaskPayload {
    title: string;
    description: string;
    status: TaskStatus;
    category: number;
}