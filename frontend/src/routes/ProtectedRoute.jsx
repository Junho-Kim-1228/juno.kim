import { Redirect, Route } from 'react-router-dom'

import { LoadingState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function ProtectedRoute({ component: Component, staffOnly = false, fallbackPath = '/', ...rest }) {
  const { user, loading } = useAuth()
  return <Route {...rest} render={(props) => {
    if (loading) return <LoadingState />
    if (!user) return <Redirect to={{ pathname: '/login', state: { from: props.location.pathname } }} />
    if (staffOnly && !user.is_staff) return <Redirect to={fallbackPath} />
    return <Component {...props} />
  }} />
}
