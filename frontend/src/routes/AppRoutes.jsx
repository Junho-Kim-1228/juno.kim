import { Redirect, Route, Switch } from 'react-router-dom'

import { MainLayout } from '../layouts/MainLayout'
import { HomePage } from '../pages/HomePage'
import { DeveloperPage } from '../pages/DeveloperPage'
import { GuestbookPage } from '../pages/GuestbookPage'
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
    <Route exact path="/guestbook" component={GuestbookPage} />
    <Route exact path="/developer" component={DeveloperPage} />
    <Redirect exact from="/records" to="/developer" />
    <Route exact path="/login" component={LoginPage} />
    <Route exact path="/register" component={RegisterPage} />
    <Route exact path="/verify-email" component={VerifyEmailPage} />
    <ProtectedRoute exact path="/profile" component={ProfilePage} />
    <ProtectedRoute exact path="/projects/new" component={ProjectEditorPage} staffOnly fallbackPath="/projects" />
    <ProtectedRoute exact path="/projects/:slug/edit" component={ProjectEditorPage} staffOnly fallbackPath="/projects" />
    <Route exact path="/projects/:slug" component={ProjectDetailPage} />
    <Route exact path="/projects" component={ProjectsPage} />
    <ProtectedRoute exact path="/board/new" component={PostEditorPage} verifiedOnly fallbackPath="/profile" />
    <ProtectedRoute exact path="/board/:slug/edit" component={PostEditorPage} verifiedOnly fallbackPath="/profile" />
    <Route exact path="/board/:slug" component={PostDetailPage} />
    <Route exact path="/board" render={() => <PostsPage allowMemberWriting />} />
    <ProtectedRoute exact path="/blog/new" component={PostEditorPage} staffOnly fallbackPath="/developer" />
    <ProtectedRoute exact path="/blog/:slug/edit" component={PostEditorPage} staffOnly fallbackPath="/developer" />
    <Route exact path="/blog/:slug" component={PostDetailPage} />
    <Redirect exact from="/blog" to="/developer" />
    <Route component={NotFoundPage} />
  </Switch></MainLayout>
}
