import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ForgotPasswordSentView from '@/views/ForgotPasswordSentView.vue'
import ForgotPasswordResendView from '@/views/ForgotPasswordResendView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import SettingsView from '@/views/SettingsView.vue'
import DashboardView from '@/views/DashboardView.vue'
import SmartSchedulerView from '@/views/SmartSchedulerView.vue'
import AIExtractorView from '@/views/AIExtractorView.vue'

const isAuthenticated = () => !!localStorage.getItem('access_token')

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            redirect: '/login',
        },

        // ===== AUTH PAGES =====
        {
            path: '/login',
            component: LoginView,
        },
        {
            path: '/register',
            component: RegisterView,
        },
        {
            path: '/forgot-password',
            component: ForgotPasswordView,
        },
        {
            path: '/forgot-password/sent',
            component: ForgotPasswordSentView,
        },
        {
            path: '/forgot-password/resend',
            component: ForgotPasswordResendView,
        },
        {
            path: '/reset-password',
            component: ResetPasswordView,
        },
        {
            path: '/',
            component: MainLayout,
            meta: { requiresAuth: true },
            children: [
                {
                    path: 'dashboard',
                    name: 'dashboard',
                    component: DashboardView,
                },
                {
                    path: 'scheduler',
                    name: 'scheduler',
                    component: SmartSchedulerView,
                },
                {
                    path: 'extractor',
                    name: 'extractor',
                    component: AIExtractorView,
                },
                {
                    path: 'settings',
                    name: 'settings',
                    component: SettingsView,
                },
            ],
        },
    ],
})

router.beforeEach((to, _from, next) => {
    if (to.meta.requiresAuth && !isAuthenticated()) {
        next('/login')
        return
    }

    if (to.path === '/login' && isAuthenticated()) {
        next('/dashboard')
        return
    }

    next()
})

export default router