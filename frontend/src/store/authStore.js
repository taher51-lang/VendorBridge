import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,

      setAuth: (token, refreshToken, user) =>
        set({ token, refreshToken, user }),

      setUser: (user) => set({ user }),

      logout: () => set({ token: null, refreshToken: null, user: null }),
    }),
    {
      name: 'vendorbridge-auth',
    }
  )
)

export default useAuthStore
