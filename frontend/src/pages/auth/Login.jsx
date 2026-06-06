import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { authApi } from '../../api/authApi'
import useAuthStore from '../../store/authStore'

export default function Login() {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const onSubmit = async (data) => {
    setLoading(true)
    setError('')
    try {
      const res = await authApi.login(data)
      const { access_token, refresh_token, user } = res.data.data
      setAuth(access_token, refresh_token, user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-2xl font-semibold text-zinc-900">⬡ VendorBridge</span>
          <p className="text-zinc-500 text-sm mt-1">Procurement & Vendor Management</p>
        </div>

        <Card className="border-zinc-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Sign in</CardTitle>
            <CardDescription>Enter your credentials to access your account</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">
                  Email
                </label>
                <Input
                  type="email"
                  placeholder="you@company.com"
                  {...register('email', { required: 'Email is required' })}
                  className={errors.email ? 'border-red-400' : ''}
                />
                {errors.email && (
                  <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium text-zinc-700">Password</label>
                  <Link to="/forgot-password" className="text-xs text-violet-600 hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <Input
                  type="password"
                  placeholder="••••••••"
                  {...register('password', { required: 'Password is required' })}
                  className={errors.password ? 'border-red-400' : ''}
                />
                {errors.password && (
                  <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <Button type="submit" className="w-full bg-zinc-900 hover:bg-zinc-800" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            <p className="text-center text-sm text-zinc-500 mt-4">
              Don't have an account?{' '}
              <Link to="/register" className="text-violet-600 hover:underline font-medium">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
