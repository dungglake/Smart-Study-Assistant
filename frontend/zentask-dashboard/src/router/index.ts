import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import SmartSchedulerView from '@/views/SmartSchedulerView.vue'
import AIExtractorView from '@/views/AIExtractorView.vue'

const isAuthenticated = () => localStorage.getItem('isLoggedIn') === 'true'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            redirect: '/login',
        },
        {
            path: '/login',
            name: 'login',
            component: LoginView,
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: DashboardView,
            meta: { requiresAuth: true },
        },
        {
            path: '/scheduler',
            name: 'scheduler',
            component: SmartSchedulerView,
            meta: { requiresAuth: true },
        },
        {
            path: '/extractor',
            name: 'extractor',
            component: AIExtractorView,
            meta: { requiresAuth: true },
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