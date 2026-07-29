import { Route, Switch } from 'react-router-dom'

import { MainLayout } from '../layouts/MainLayout'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { PostDetailPage } from '../pages/PostDetailPage'
import { PostEditorPage } from '../pages/PostEditorPage'
import { PostsPage } from '../pages/PostsPage'
import { ProfilePage } from '../pages/ProfilePage'
import { ProjectDetailPage } from '../pages/ProjectDetailPage'
import { ProjectEditorPage } from '../pages/ProjectEditorPage'
import { ProjectsPage } from '../pages/ProjectsPage'
import { RegisterPage } from '../pages/RegisterPage'
import { VerifyEmailPage } from '../pages/VerifyEmailPage'
import { ProtectedRoute } from './ProtectedRoute'

export function AppRoutes() {
  return <MainLayout><Switch>
    <Route exact path="/" component={HomePage} />
    <Route exact path="/login" component={LoginPage} />
    <Route exact path="/register" component={RegisterPage} />
    <Route exact path="/verify-email" component={VerifyEmailPage} />
    <ProtectedRoute exact path="/profile" component={ProfilePage} />
    <ProtectedRoute exact path="/projects/new" component={ProjectEditorPage} staffOnly fallbackPath="/projects" />
    <ProtectedRoute exact path="/projects/:slug/edit" component={ProjectEditorPage} staffOnly fallbackPath="/projects" />
    <Route exact path="/projects/:slug" component={ProjectDetailPage} />
    <Route exact path="/projects" component={ProjectsPage} />
    <ProtectedRoute exact path="/blog/new" component={PostEditorPage} staffOnly fallbackPath="/blog" />
    <ProtectedRoute exact path="/blog/:slug/edit" component={PostEditorPage} staffOnly fallbackPath="/blog" />
    <Route exact path="/blog/:slug" component={PostDetailPage} />
    <Route exact path="/blog" component={PostsPage} />
    <Route component={NotFoundPage} />
  </Switch></MainLayout>
}
