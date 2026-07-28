import { Redirect, Route } from 'react-router-dom'

import { LoadingState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function ProtectedRoute({ component: Component, ...rest }) {
  const { user, loading } = useAuth()
  return <Route {...rest} render={(props) => loading ? <LoadingState /> : user ? <Component {...props} /> : <Redirect to={{ pathname: '/login', state: { from: props.location.pathname } }} />} />
}
