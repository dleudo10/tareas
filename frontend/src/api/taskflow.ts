import axios from "axios";

import type {
    Category,
    Task,
    TaskPayload,
} from "../types";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 10000,
    headers: {
        "Content-Type": "application/json",
    },
});

function withToken(token: string) {
    return {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    };
}

export async function getTasks(
    token: string,
): Promise<Task[]> {
    const response = await api.get<Task[]>(
        "tasks/",
        withToken(token),
    );

    return response.data;
}

export async function getCategories(
    token: string,
): Promise<Category[]> {
    const response = await api.get<Category[]>(
        "categories/",
        withToken(token),
    );

    return response.data;
}

export async function createTask(
    token: string,
    payload: TaskPayload,
): Promise<Task> {
    const response = await api.post<Task>(
        "tasks/",
        payload,
        withToken(token),
    );

    return response.data;
}

export async function updateTask(
    token: string,
    taskId: number,
    payload: TaskPayload,
): Promise<Task> {
    const response = await api.patch<Task>(
        `tasks/${taskId}/`,
        payload,
        withToken(token),
    );

    return response.data;
}

export async function deleteTask(
    token: string,
    taskId: number,
): Promise<void> {
    await api.delete(
        `tasks/${taskId}/`,
        withToken(token),
    );
}