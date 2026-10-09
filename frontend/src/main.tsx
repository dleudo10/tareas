import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import {
    AuthProvider,
    type AuthProviderProps,
} from "react-oidc-context";

import './index.css'
import App from './App.tsx'

// Aquí utilizamos el flujo Authorization Code con PKCE. 
// El usuario se redirige a OLIMPO para autenticarse; al regresar, 
// la librería procesa la respuesta y proporciona el token al frontend.

const oidcConfig: AuthProviderProps = {
    authority: import.meta.env.VITE_OIDC_AUTHORITY,
    client_id: import.meta.env.VITE_OIDC_CLIENT_ID,
    redirect_uri: import.meta.env.VITE_OIDC_REDIRECT_URI,
    post_logout_redirect_uri:
        import.meta.env.VITE_OIDC_POST_LOGOUT_REDIRECT_URI,

    response_type: "code",
    scope: import.meta.env.VITE_OIDC_SCOPE,

    onSigninCallback: () => {
        window.history.replaceState(
        {},
        document.title,
        "/taskflow/"
        );
    },
};

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<AuthProvider {...oidcConfig}>
			<App />
		</AuthProvider>
	</StrictMode>,
)
