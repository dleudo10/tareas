import {
    useCallback,
    useEffect,
    useState,
    type FormEvent,
} from "react";

import { useAuth } from "react-oidc-context";

import {
    createTask,
    deleteTask,
    getCategories,
    getTasks,
    updateTask,
} from "./api/taskflow";

import type {
    Category,
    Task,
    TaskPayload,
    TaskStatus,
} from "./types";

const emptyForm: TaskPayload = {
    title: "",
    description: "",
    status: "PENDING",
    category: 0,
};

function getErrorMessage(error: unknown): string {
    if (
        typeof error === "object" &&
        error !== null &&
        "response" in error
    ) {
        const response = (
            error as {
                response?: {
                    data?: {
                        detail?: string;
                    };
                };
            }
        ).response;

        if (response?.data?.detail) {
            return response.data.detail;
        }
    }

    return "Ocurrió un error. Verifica la conexión y vuelve a intentarlo.";
}

const statusLabels: Record<TaskStatus, string> = {
    PENDING: "Pendiente",
    IN_PROGRESS: "En progreso",
    COMPLETED: "Completada",
};

export default function App() {
    const auth = useAuth();

    const token = auth.user?.access_token;

    const [tasks, setTasks] = useState<Task[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);

    const [form, setForm] = useState<TaskPayload>(emptyForm);
    const [editingId, setEditingId] = useState<number | null>(null);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    const loadData = useCallback(async () => {
        if (!token) return;

        setLoading(true);
        setError("");

        try {
            const [taskData, categoryData] = await Promise.all([
                getTasks(token),
                getCategories(token),
            ]);

            setTasks(taskData);
            setCategories(categoryData);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        if (auth.isAuthenticated && token) {
            void loadData();
        }
    }, [auth.isAuthenticated, token, loadData]);

    function resetForm() {
        setForm(emptyForm);
        setEditingId(null);
    }

    function startEditing(task: Task) {
        setEditingId(task.id);

        setForm({
            title: task.title,
            description: task.description,
            status: task.status,
            category: task.category,
        });

        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        if (!token) return;

        setSaving(true);
        setError("");

        try {
            if (editingId !== null) {
                await updateTask(token, editingId, form);
            } else {
                await createTask(token, form);
            }

            resetForm();
            await loadData();
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(task: Task) {
        if (!token) return;

        const confirmed = window.confirm(
            `¿Deseas eliminar la tarea "${task.title}"?`,
        );

        if (!confirmed) return;

        setError("");

        try {
            await deleteTask(token, task.id);
            await loadData();
        } catch (err) {
            setError(getErrorMessage(err));
        }
    }

    if (auth.isLoading) {
        return (
            <main className="page">
                <p>Verificando sesión con OLIMPO...</p>
            </main>
        );
    }

    if (auth.error) {
        return (
            <main className="page">
                <h1>No se pudo completar el inicio de sesión</h1>
                <p>{auth.error.message}</p>
                <button onClick={() => void auth.signinRedirect()}>
                    Volver a intentar
                </button>
            </main>
        );
    }

    if (!auth.isAuthenticated) {
        return (
            <main className="login-page">
                <section className="login-card">
                    <p className="eyebrow">OLIMPO · APLICACIÓN INTEGRADA</p>
                    <h1>TaskFlow</h1>
                    <p>
                        Administra tus tareas desde una aplicación
                        conectada al sistema de identidad de OLIMPO.
                    </p>

                    <button
                        className="primary-button"
                        onClick={() => void auth.signinRedirect()}
                    >
                        Iniciar sesión con OLIMPO
                    </button>
                </section>
            </main>
        );
    }

    const currentUser =
        auth.user?.profile.preferred_username ??
        auth.user?.profile.name ??
        auth.user?.profile.sub ??
        "Usuario";

    return (
        <main className="page">
            <header className="topbar">
                <div>
                    <p className="eyebrow">GESTIÓN PERSONAL</p>
                    <h1>TaskFlow</h1>
                </div>

                <div className="user-actions">
                    <span>{currentUser}</span>

                    <button
                        className="secondary-button"
                        onClick={() => void auth.signoutRedirect()}
                    >
                        Cerrar sesión
                    </button>
                </div>
            </header>

            {error && (
                <div className="error-message" role="alert">
                    {error}
                </div>
            )}

            <section className="panel">
                <div className="section-heading">
                    <div>
                        <h2>
                            {editingId === null
                                ? "Crear tarea"
                                : "Editar tarea"}
                        </h2>

                        <p>
                            Las categorías disponibles dependen de tus
                            permisos en TaskFlow.
                        </p>
                    </div>
                </div>

                <form className="task-form" onSubmit={handleSubmit}>
                    <label>
                        Título
                        <input
                            required
                            maxLength={200}
                            value={form.title}
                            onChange={(event) =>
                                setForm({
                                    ...form,
                                    title: event.target.value,
                                })
                            }
                            placeholder="Ej. Revisar documentación"
                        />
                    </label>

                    <label>
                        Descripción
                        <textarea
                            value={form.description}
                            onChange={(event) =>
                                setForm({
                                    ...form,
                                    description: event.target.value,
                                })
                            }
                            rows={3}
                            placeholder="Describe la tarea..."
                        />
                    </label>

                    <div className="form-row">
                        <label>
                            Categoría
                            <select
                                required
                                value={form.category || ""}
                                onChange={(event) =>
                                    setForm({
                                        ...form,
                                        category: Number(event.target.value),
                                    })
                                }
                            >
                                <option value="" disabled>
                                    Selecciona una categoría
                                </option>

                                {categories.map((category) => (
                                    <option
                                        key={category.id}
                                        value={category.id}
                                    >
                                        {category.name}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label>
                            Estado
                            <select
                                value={form.status}
                                onChange={(event) =>
                                    setForm({
                                        ...form,
                                        status: event.target.value as TaskStatus,
                                    })
                                }
                            >
                                <option value="PENDING">Pendiente</option>
                                <option value="IN_PROGRESS">En progreso</option>
                                <option value="COMPLETED">Completada</option>
                            </select>
                        </label>
                    </div>

                    {categories.length === 0 && (
                        <p className="helper-text">
                            No tienes categorías disponibles. Revisa las
                            categorías activas y sus asociaciones de roles
                            en el administrador de Django.
                        </p>
                    )}

                    <div className="form-actions">
                        <button
                            className="primary-button"
                            type="submit"
                            disabled={
                                saving ||
                                categories.length === 0
                            }
                        >
                            {saving
                                ? "Guardando..."
                                : editingId === null
                                  ? "Crear tarea"
                                  : "Guardar cambios"}
                        </button>

                        {editingId !== null && (
                            <button
                                className="secondary-button"
                                type="button"
                                onClick={resetForm}
                            >
                                Cancelar edición
                            </button>
                        )}
                    </div>
                </form>
            </section>

            <section className="panel">
                <div className="section-heading">
                    <div>
                        <h2>Tareas</h2>
                        <p>
                            {tasks.length} tarea(s) devuelta(s) por el servidor.
                        </p>
                    </div>

                    <button
                        className="secondary-button"
                        onClick={() => void loadData()}
                        disabled={loading}
                    >
                        {loading ? "Actualizando..." : "Actualizar"}
                    </button>
                </div>

                {loading ? (
                    <p>Cargando tareas...</p>
                ) : tasks.length === 0 ? (
                    <div className="empty-state">
                        <h3>No hay tareas para mostrar</h3>
                        <p>Crea tu primera tarea utilizando el formulario.</p>
                    </div>
                ) : (
                    <div className="task-list">
                        {tasks.map((task) => (
                            <article className="task-card" key={task.id}>
                                <div className="task-content">
                                    <div className="task-title-row">
                                        <h3>{task.title}</h3>

                                        <span
                                            className={`status status-${task.status.toLowerCase()}`}
                                        >
                                            {statusLabels[task.status]}
                                        </span>
                                    </div>

                                    <p className="task-description">
                                        {task.description ||
                                            "Sin descripción."}
                                    </p>

                                    <div className="task-meta">
                                        <span>{task.category_name}</span>
                                        <span>
                                            Creada por {task.owner_username}
                                        </span>
                                    </div>
                                </div>

                                <div className="task-actions">
                                    <button
                                        className="secondary-button"
                                        onClick={() => startEditing(task)}
                                    >
                                        Editar
                                    </button>

                                    <button
                                        className="danger-button"
                                        onClick={() => void handleDelete(task)}
                                    >
                                        Eliminar
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </section>
        </main>
    );
}