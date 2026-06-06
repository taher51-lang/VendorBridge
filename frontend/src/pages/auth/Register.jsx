import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { authApi } from '../../api/authApi'

export default function Register() {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onSubmit = async (data) => {
    setLoading(true)
    setError('')
    try {
      await authApi.register(data)
      navigate('/login', { state: { message: 'Account created! Please sign in.' } })
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.')
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
            <CardTitle className="text-xl">Create account</CardTitle>
            <CardDescription>Fill in your details to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Full name</label>
                <Input
                  placeholder="John Smith"
                  {...register('full_name', { required: 'Full name is required' })}
                  className={errors.full_name ? 'border-red-400' : ''}
                />
                {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Email</label>
                <Input
                  type="email"
                  placeholder="you@company.com"
                  {...register('email', { required: 'Email is required' })}
                  className={errors.email ? 'border-red-400' : ''}
                />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Role</label>
                <Select onValueChange={(val) => setValue('role', val)}>
                  <SelectTrigger className={errors.role ? 'border-red-400' : ''}>
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="procurement_officer">Procurement Officer</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                    <SelectItem value="vendor">Vendor</SelectItem>
                  </SelectContent>
                </Select>
                {errors.role && <p className="text-red-500 text-xs mt-1">{errors.role.message}</p>}
              </div>

              <div>
                <label className="text-sm font-medium text-zinc-700 block mb-1.5">Password</label>
                <Input
                  type="password"
                  placeholder="Min. 8 characters"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Password must be at least 8 characters' }
                  })}
                  className={errors.password ? 'border-red-400' : ''}
                />
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <Button type="submit" className="w-full bg-zinc-900 hover:bg-zinc-800" disabled={loading}>
                {loading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>

            <p className="text-center text-sm text-zinc-500 mt-4">
              Already have an account?{' '}
              <Link to="/login" className="text-violet-600 hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
